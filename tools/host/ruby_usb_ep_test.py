#!/usr/bin/env python3
"""CL-0331 EP0 0x2E endpoint test channel driver (rubyep_test=1).

Protocol
  host -> device  0x40/0x2E  ascii "t331 <cmd> ..."
  device -> host  0xC0/0x31  16 x u32 mailbox:
                  [0] magic 'T331', [1] seq, [2] cmd, [3] status,
                  [4..15] payload

The mailbox read is the only EP0 traffic the test path adds; bulk data
uses the existing EP1 echo loopback (owner=echo).  Single reader, 5 ms
pacing, clear-halt once at start, EP0 availability checked around every
step.

Examples
  ruby_usb_ep_test.py --caps
  ruby_usb_ep_test.py --owner-echo --queue 512 --readback 512 --crc
  ruby_usb_ep_test.py --matrix lite
"""
import argparse
import struct
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
EP_OUT, EP_IN = 0x01, 0x81
MPS = 512
MAGIC = 0x31333354

CMD_NAMES = {
    1: "caps", 2: "stat", 3: "conf", 4: "queue", 5: "halt", 6: "clear",
    7: "stop", 8: "start", 9: "crc", 10: "resetcrc", 11: "drain",
    12: "owner", 13: "rxreset",
}


def fnv1a(data):
    h = 2166136261
    for b in data:
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return h


class Device:
    def __init__(self):
        dev = usb.core.find(idVendor=VID, idProduct=PID, backend=BACKEND)
        if dev is None:
            raise SystemExit("NO_DEVICE %04x:%04x" % (VID, PID))
        self.dev = dev
        usb.util.claim_interface(dev, 0)
        # The mailbox keeps the last reply across processes: take a seq
        # baseline so an old box can never be mistaken for the reply.
        try:
            box = self.read_box()
            self.seq = box[1] if box[0] == MAGIC else 0
        except Exception:
            self.seq = 0
        self.drain()

    def cmd(self, text, code=None, timeout=3.0):
        base = self.seq
        self.dev.ctrl_transfer(0x40, 0x2E, 1, 0, text.encode(), timeout=1500)
        deadline = time.time() + timeout
        while time.time() < deadline:
            box = self.read_box()
            if box[0] == MAGIC and box[1] != base:
                self.seq = box[1]
                if code is not None and box[2] != code:
                    # a stale/late reply; keep waiting for ours
                    base = box[1]
                    continue
                return box
            time.sleep(0.005)
        raise SystemExit("no mailbox reply for %r" % text)

    def read_box(self):
        raw = bytes(self.dev.ctrl_transfer(0xC0, 0x31, 0, 0, 64,
                                           timeout=1500))
        return struct.unpack("<16I", raw)

    def write(self, data):
        for off in range(0, len(data), MPS):
            self.dev.write(EP_OUT, data[off:off + MPS], timeout=2000)

    def read(self, want, timeout=5.0):
        buf = bytearray()
        deadline = time.time() + timeout
        while len(buf) < want and time.time() < deadline:
            try:
                buf += bytes(self.dev.read(EP_IN, 4096, timeout=100))
            except usb.core.USBTimeoutError:
                pass
        return bytes(buf)

    def drain(self):
        while True:
            try:
                self.dev.read(EP_IN, 4096, timeout=50)
            except usb.core.USBTimeoutError:
                return


def pattern(n):
    return bytes(i & 0xFF for i in range(n))


def check_box(box, code, what):
    if box[0] != MAGIC:
        raise SystemExit("%s: bad magic %08x" % (what, box[0]))
    if box[2] != code:
        raise SystemExit("%s: cmd %u != %u" % (what, box[2], code))
    if box[3] not in (0, 110):
        raise SystemExit("%s: status %u" % (what, box[3]))
    if box[3] == 110:
        raise SystemExit("%s: timeout (110)" % what)
    return box


def stat_summary(box):
    return ("ready/rx=%u inf=%u rxpk=%u rxbytes=%u rxerr=%u zlp=%u "
            "enq=%u deq=%u tq=%08x rq=%08x cur=%02x/%02x rxdeq=%02x" % (
                box[4] & 1, (box[4] >> 8) & 0xffff, box[5], box[6],
                box[7] & 0xffff, box[7] >> 16, box[8] & 0xffff,
                box[8] >> 16, box[9], box[10], box[11] & 0xff,
                (box[11] >> 8) & 0xff, (box[11] >> 16) & 0xff))


def run_loop(dev, length, pace=0.005):
    data = pattern(length)
    dev.drain()
    dev.cmd("t331 resetcrc", code=10)
    for off in range(0, length, MPS):
        dev.write(data[off:off + MPS])
        time.sleep(pace)
    got = dev.read(length, timeout=8.0)
    time.sleep(0.1)
    box = check_box(dev.cmd("t331 crc"), 9, "crc")
    dev_crc, rxpk, rxbytes, rxerr = box[4], box[5], box[6], box[7]
    ok_len = len(got) == length
    ok_data = got == data
    ok_crc = dev_crc == fnv1a(data)
    ok_err = rxerr == 0
    print("len=%-6u read=%-6u %s crc=%08x/%08x %s rxpk=%u rxbytes=%u "
          "rxerr=%u %s" % (length, len(got),
                           "DATA-OK" if ok_data else "DATA-DIFF",
                           dev_crc, fnv1a(data),
                           "CRC-OK" if ok_crc else "CRC-BAD",
                           rxpk, rxbytes, rxerr,
                           "OK" if (ok_len and ok_data and ok_crc and
                                    ok_err) else "FAIL"))
    return ok_len and ok_data and ok_crc and ok_err


def matrix(dev, tier):
    print("== T0 caps/stat")
    caps = check_box(dev.cmd("t331 caps"), 1, "caps")
    print("caps ep0=%u tx=%u rx=%u info=%u eps=%u" %
          (caps[4], caps[5], caps[6], caps[7], caps[8]))
    print("stat:", stat_summary(check_box(dev.cmd("t331 stat"), 2, "stat")))
    print("== T4 clear-halt once + owner echo")
    check_box(dev.cmd("t331 clear"), 6, "clear")
    check_box(dev.cmd("t331 owner echo"), 12, "owner")
    check_box(dev.cmd("t331 drain 2000"), 11, "drain")
    # one warm-up transfer: the first echo after an owner switch can take
    # one workloop round before the TX primer runs; it is not a gate.
    dev.drain()
    dev.write(pattern(64))
    dev.read(64, timeout=3.0)
    dev.drain()
    check_box(dev.cmd("t331 drain 2000"), 11, "drain")
    print("== T1 lengths")
    ok = True
    for length in (512, 1024, 4096, 16384):
        ok = run_loop(dev, length) and ok
    if tier == "lite":
        print("== T3 one geometry variant")
        check_box(dev.cmd("t331 drain 2000"), 11, "drain")
        box = check_box(dev.cmd("t331 conf 32 8 4096"), 3, "conf")
        print("conf 32/8/4096 status=%u" % box[3])
        ok = run_loop(dev, 4096, pace=0.002) and ok
        check_box(dev.cmd("t331 conf 64 16 512"), 3, "conf-restore")
    else:
        print("== T3 ring/inflight/gpd matrix")
        for ring, inf, gpd in ((16, 8, 512), (32, 8, 1024),
                               (64, 16, 4096), (64, 32, 8192)):
            check_box(dev.cmd("t331 drain 2000"), 11, "drain")
            box = check_box(dev.cmd("t331 conf %u %u %u" %
                                    (ring, inf, gpd)), 3, "conf")
            print("conf %u/%u/%u status=%u" % (ring, inf, gpd, box[3]))
            ok = run_loop(dev, gpd) and ok
        check_box(dev.cmd("t331 conf 64 16 512"), 3, "conf-restore")
    print("== T4 stop/start")
    check_box(dev.cmd("t331 drain 2000"), 11, "drain")
    check_box(dev.cmd("t331 stop"), 7, "stop")
    check_box(dev.cmd("t331 start"), 8, "start")
    ok = run_loop(dev, 4096) and ok
    print("== gate:", "PASS" if ok else "FAIL")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caps", action="store_true")
    ap.add_argument("--stat", action="store_true")
    ap.add_argument("--owner-echo", action="store_true")
    ap.add_argument("--queue", type=int)
    ap.add_argument("--readback", type=int)
    ap.add_argument("--crc", action="store_true")
    ap.add_argument("--matrix", choices=["lite", "full"])
    ap.add_argument("--cmd")
    args = ap.parse_args()

    dev = Device()
    if args.cmd:
        box = dev.cmd(args.cmd)
        print("box:", " ".join("%08x" % w for w in box))
        return
    if args.caps:
        box = check_box(dev.cmd("t331 caps"), 1, "caps")
        print("caps ep0=%u tx=%u rx=%u info=%u eps=%u" %
              (box[4], box[5], box[6], box[7], box[8]))
    if args.stat:
        print("stat:", stat_summary(check_box(dev.cmd("t331 stat"), 2,
                                              "stat")))
    if args.owner_echo:
        check_box(dev.cmd("t331 owner echo"), 12, "owner")
    if args.queue:
        box = check_box(dev.cmd("t331 queue %u" % args.queue), 4, "queue")
        print("queue enqueued=%u" % box[3])
    if args.readback:
        got = dev.read(args.readback, timeout=5.0)
        want = pattern(args.readback)
        print("readback %u/%u %s" % (len(got), args.readback,
                                    "OK" if got == want else "DIFF"))
    if args.crc:
        box = check_box(dev.cmd("t331 crc"), 9, "crc")
        print("crc dev=%08x pk=%u bytes=%u err=%u" %
              (box[4], box[5], box[6], box[7]))
    if args.matrix:
        ok = matrix(dev, args.matrix)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()