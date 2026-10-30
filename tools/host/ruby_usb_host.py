#!/usr/bin/env python3
"""Ruby USB host session manager (v1).

Long-lived, paced EP2 IN log sessions with automatic reconnect, a one-shot
health snapshot and a command channel.  This is the host-side counterpart of
the kernel USB log channel; it never calls clear_halt and never retries in a
tight loop (both measured to knock the device off the bus).

Published reference copy: see docs/en/12-usb-host.md.  EP0 is read-only;
the only device writes are the EP2 OUT command text and the optional
--pcycle pnputil restart.  Do not add clear_halt loops or 0x2D writes.

Subcommands:
  watch   run a paced log session until Ctrl-C; auto-reconnects when the
          device re-appears (e.g. after a physical reboot).  On EPIPE the IN
          reader stops but EP0 status and the OUT command path stay alive.
  status  one-shot EP0 health snapshot (0x27 / 0x23 / 0x2B + key registers).
  cmd     send one line to EP2 OUT, then drain EP2 IN paced responses.

  python ruby_usb_host.py watch --pace-ms 5 --log session.log
  python ruby_usb_host.py status
  python ruby_usb_host.py cmd "help" --drain-secs 3
"""
import argparse
import os
import struct
import subprocess
import sys
import time

import usb.core
import usb.util
import usb.backend.libusb1

try:
    import libusb_package
    BACKEND = usb.backend.libusb1.get_backend(
        find_library=libusb_package.find_library)
except Exception:
    BACKEND = usb.backend.libusb1.get_backend()

VID, PID = 0x1209, 0x0002
EP_OUT, EP_IN = 0x02, 0x82
READ_TIMEOUT_MS = 3000

KEY_REGS = [
    ("EP_RST", 0x11201804),
    ("TX2CSR0", 0x11201120),
    ("TQCSR2", 0x11201520),
    ("TQCPR2", 0x11201528),
]


def log_line(fp, line):
    stamp = time.strftime("%H:%M:%S")
    text = "[%s] %s" % (stamp, line)
    print(text, flush=True)
    if fp:
        fp.write(text + "\n")
        fp.flush()


def clean_text(text):
    return "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)


def find_device():
    return usb.core.find(idVendor=VID, idProduct=PID, backend=BACKEND)


def device_instance_ids():
    try:
        out = subprocess.run(
            ["pnputil", "/enum-devices", "/connected"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace").stdout
    except Exception:
        return []
    ids = []
    for line in out.splitlines():
        u = line.upper()
        if "VID_1209&PID_0002" in u and "\\" in line:
            ids.append(line.split(":", 1)[-1].strip())
    return ids


def port_cycle():
    """Best-effort pnputil restart of the wedged-but-present device.

    Needs elevation; returns an action string for the caller to report.
    When the device has vanished from the bus this is a no-op (proven:
    post-abort the host will not re-enumerate, only a device reboot helps).
    """
    ids = device_instance_ids()
    if not ids:
        return "no device instance to restart"
    results = []
    for dev_id in ids:
        try:
            r = subprocess.run(
                ["pnputil", "/restart-device", dev_id],
                capture_output=True, text=True, timeout=60)
            results.append("%s: rc=%d %s" % (dev_id, r.returncode,
                                             (r.stdout or r.stderr).strip()))
        except Exception as e:
            results.append("%s: %r" % (dev_id, e))
    return "; ".join(results)


class Session:
    def __init__(self, pace_ms=5.0, log_path=None, pcycle=False):
        self.pace_ms = pace_ms
        self.pcycle = pcycle
        self.fp = open(log_path, "a", encoding="utf-8") if log_path else None
        self.dev = None
        self.connected = False
        self.in_dead = False
        self.seq = []
        self.frames = 0

    # ---- lifecycle ---------------------------------------------------
    def connect(self, verbose=True):
        try:
            if self.dev is not None:
                try:
                    usb.util.release_interface(self.dev, 0)
                except Exception:
                    pass
                try:
                    usb.util.dispose_resources(self.dev)
                except Exception:
                    pass
                self.dev = None
            dev = find_device()
            if dev is None:
                self.connected = False
                return False
            usb.util.claim_interface(dev, 0)
            self.dev = dev
            self.connected = True
            self.in_dead = False
            self.seq = []
            self.frames = 0
            if verbose:
                log_line(self.fp, "[connected] EP OUT 0x02 / IN 0x82 pace=%.1fms"
                         % self.pace_ms)
            return True
        except Exception as e:
            self.connected = False
            log_line(self.fp, "[connect] %r" % (e,))
            return False

    def close(self):
        self.connected = False
        if self.fp:
            self.fp.close()
            self.fp = None
        if self.dev is not None:
            try:
                usb.util.release_interface(self.dev, 0)
            except Exception:
                pass
            try:
                usb.util.dispose_resources(self.dev)
            except Exception:
                pass
            self.dev = None

    def summary(self):
        got = len(self.seq)
        holes = dup = 0
        if got > 1:
            seen = set()
            expect = self.seq[0]
            for s in self.seq:
                if s in seen:
                    dup += 1
                elif s != expect:
                    holes += 1
                seen.add(s)
                expect = s + 1
        return "frames=%d unique=%d holes=%d dup=%d" % (
            self.frames, got, holes, dup)

    # ---- EP0 ----------------------------------------------------------
    def ctrl(self, req, n, wValue=0, wIndex=0):
        if self.dev is None:
            raise RuntimeError("not connected")
        return bytes(self.dev.ctrl_transfer(
            0xC0, req, wValue, wIndex, n, timeout=READ_TIMEOUT_MS))

    def status(self):
        try:
            v = struct.unpack("<16I", self.ctrl(0x27, 64))
            log_line(self.fp,
                     "0x27 setups=%d txpkts=%d dataends=%d sentstalls=%d "
                     "busresets=%d cfg/ready=%08x"
                     % (v[1], v[4], v[5], v[6], v[8], v[9]))
            r = struct.unpack("<16I", self.ctrl(0x23, 64))
            log_line(self.fp,
                     "0x23 packets=%d bytes=%d zlp=%d last=%d deq=%d hwo=%x "
                     "errors=%d"
                     % (r[1], r[2], r[3], r[4], r[15] & 0xf,
                        (r[15] >> 4) & 0xf, r[13]))
            h = struct.unpack("<8I", self.ctrl(0x2B, 32))
            log_line(self.fp, "0x2B log_total=%d" % (h[3] | (h[4] << 32)))
            regs = " ".join("%s=%08x" % (nm, self.probe_read(addr))
                            for nm, addr in KEY_REGS)
            log_line(self.fp, "regs " + regs)
        except Exception as e:
            log_line(self.fp, "[status] %r" % (e,))

    def probe_read(self, addr):
        b = self.ctrl(0x2C, 4, wValue=addr & 0xFFFF, wIndex=(addr >> 16) & 0xFFFF)
        if len(b) != 4:
            raise RuntimeError("short probe read %r" % (b,))
        return struct.unpack("<I", b)[0]

    # ---- EP2 ----------------------------------------------------------
    def send(self, line):
        if not self.connected or self.dev is None:
            return "[offline]"
        try:
            self.dev.write(EP_OUT, (line + "\n").encode(),
                           timeout=READ_TIMEOUT_MS)
            if self.fp:
                self.fp.write(">> %s\n" % line)
                self.fp.flush()
            return None
        except Exception as e:
            self.connected = False
            return "[ep2-out] %r" % (e,)

    def handle_frame(self, data):
        if len(data) < 16:
            log_line(self.fp, "[short] %d B %s" % (len(data), data.hex()))
            return
        seq = struct.unpack_from("<H", data, 0)[0]
        self.seq.append(seq)
        self.frames += 1
        text = clean_text(
            data[16:].split(b"\x00", 1)[0].decode("utf-8", "replace"))
        for line in text.splitlines():
            if line.strip():
                log_line(self.fp, "[%05d] %s" % (seq, line.rstrip()))

    def abort_snapshot(self):
        """EP0 counter sample in the seconds window after an EP2 abort.

        0x21/0x22/0x23 + TX queue registers answer whether the ring was
        full/stalled when the host fired the XACT.  The kernel packs the
        0x22 inflight/enq/deq fields as 4-bit truncations, so derive the
        true outstanding count from push_seq - txdone; never read the
        inflight nibble as a full count (0142 conclusion was misread).
        """
        st = None
        try:
            st = struct.unpack("<16I", self.ctrl(0x21, 64))
            log_line(self.fp, "0x21 v=%s"
                     % " ".join("%08x" % x for x in st[:8]))
        except Exception as e:
            log_line(self.fp, "[snap] 0x21 %r" % (e,))
        try:
            v = struct.unpack("<16I", self.ctrl(0x23, 64))
            log_line(self.fp, "0x23 v=%s"
                     % " ".join("%08x" % x for x in v[:8]))
        except Exception as e:
            log_line(self.fp, "[snap] 0x23 %r" % (e,))
        try:
            v = struct.unpack("<8I", self.ctrl(0x22, 32))
            # "EP2D": v2 = hiar | hwo_count<<8 | inflight[3:0]<<16 |
            #         enq[3:0]<<20 | deq[3:0]<<24
            push_seq = (st[1] & 0xffff) if st else None
            outstanding = (push_seq - v[3]) if push_seq is not None else None
            log_line(self.fp,
                     "0x22 txcpr=%08x hwo=%d inflight_nibble=%d "
                     "enq_nibble=%d deq_nibble=%d txdone=%d "
                     "push_seq=%s outstanding=%s recoveries=%d qisar0=%08x"
                     % (v[1], (v[2] >> 8) & 0xff, (v[2] >> 16) & 0xf,
                        (v[2] >> 20) & 0xf, (v[2] >> 24) & 0xf,
                        v[3], push_seq, outstanding, v[4], v[5]))
        except Exception as e:
            log_line(self.fp, "[snap] 0x22 %r" % (e,))
        try:
            regs = " ".join("%s=%08x" % (nm, self.probe_read(addr))
                            for nm, addr in KEY_REGS)
            log_line(self.fp, "regs " + regs)
        except Exception as e:
            log_line(self.fp, "[snap] regs %r" % (e,))

    def drain(self, secs, quiet_idle=True):
        end = time.time() + secs
        idle_since = time.time()
        while time.time() < end:
            try:
                data = bytes(self.dev.read(EP_IN, 512, timeout=200))
            except Exception as e:
                msg = str(e).lower()
                if "timeout" in msg or "timed out" in msg:
                    continue
                if "pipe error" in msg or "errno 32" in msg:
                    self.in_dead = True
                    log_line(self.fp, "[ep2-in] %r (halted; EP0 stays usable)"
                             % (e,))
                    self.abort_snapshot()
                else:
                    self.connected = False
                    log_line(self.fp, "[ep2-in] %r (device gone)" % (e,))
                return
            idle_since = time.time()
            self.handle_frame(data)
            if self.pace_ms > 0:
                time.sleep(self.pace_ms / 1000.0)

    def watch(self):
        backoff = 1.0
        cycled = False
        while True:
            if not self.connected and not self.connect():
                if self.pcycle and not cycled:
                    log_line(self.fp, "[pcycle] " + port_cycle())
                    cycled = True
                time.sleep(backoff)
                backoff = min(backoff * 2, 15.0)
                continue
            backoff = 1.0
            cycled = False
            self.status()
            self.drain(3600)
            if self.connected:
                log_line(self.fp, "[session] " + self.summary())
            log_line(self.fp, "[reconnect] waiting for 1209:0002 ...")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="op", required=True)

    w = sub.add_parser("watch")
    w.add_argument("--pace-ms", type=float, default=5.0)
    w.add_argument("--log", default=None)
    w.add_argument("--pcycle", action="store_true",
                   help="one pnputil restart attempt when the device is "
                        "wedged but still enumerated")

    s = sub.add_parser("status")

    c = sub.add_parser("cmd")
    c.add_argument("line")
    c.add_argument("--drain-secs", type=float, default=3.0)
    c.add_argument("--pace-ms", type=float, default=5.0)

    a = ap.parse_args()
    if a.op == "watch":
        sess = Session(pace_ms=a.pace_ms, log_path=a.log, pcycle=a.pcycle)
        try:
            sess.watch()
        except KeyboardInterrupt:
            log_line(sess.fp, "[stopped] " + sess.summary())
        finally:
            sess.close()
    elif a.op == "status":
        sess = Session()
        try:
            if not sess.connect(verbose=False):
                print("NO_DEVICE 1209:0002")
                return 1
            sess.status()
        finally:
            sess.close()
    elif a.op == "cmd":
        sess = Session(pace_ms=a.pace_ms)
        try:
            if not sess.connect(verbose=False):
                print("NO_DEVICE 1209:0002")
                return 1
            err = sess.send(a.line)
            if err:
                print(err)
                return 1
            sess.drain(a.drain_secs)
            print(sess.summary())
        finally:
            sess.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
