# 12 — USB host channel: conditions, driver binding and safe debugging

**English** · [中文](../zh/12-usb-host.md)

> Status tags follow the repository README: **[measured]**, **[DTS]**,
> **[inferred]**, **[historical]**. A number without a source is a bug.
> This page describes how to operate the channel; it is not a fix for the
> open host-side XACT.

## What is verified (2026-10-30) [measured]

- Kernel 0143 (patchset `f47f4c19...`, 139 files; CI `41022192026`;
  exec-data `6fa65088...`) runs USB 2.0 device mode as a vendor-specific
  device (`1209:0002`) with one bulk OUT (`0x02`, 64-byte MPS) and one bulk
  IN (`0x82`, 512-byte MPS).
- Enumeration, SET_CONFIGURATION and High-Speed are green; the kernel emits
  one log frame per GPD: a 16-byte header plus up to 495 bytes of text =
  511 bytes (one byte below the 512-byte MPS, so every GPD ends on a short
  packet).
- The host-side first-session XACT is **still open**. A session delivers a
  variable number of frames (0-54 observed; 0 means the IN pipe was already
  halted) and then the IN URB completes with `0xC0000011` followed by
  `ABORT_PIPE`. EP0 can also hit XACT during enumeration or after the abort.
  The device may stay enumerated or drop; a physical reboot is the reliable
  recovery once it is gone.
- Host-side software and test conditions below are the reference used for
  the 0143, 0150 and 0151 runs.

## Test conditions

### Device side [measured]

- MT6877, USB 2.0 High-Speed, bus-powered from the host port.
- Vendor-specific interface, VID:PID `1209:0002`, one configuration.
- Bulk OUT `0x02` with 64-byte MPS; bulk IN `0x82` with 512-byte MPS.
- Log frames: 511 bytes each; ring: 64 GPDs, at most 63 in flight; the
  reset/rearm path resets the TX ring after stopping the QMU.
- Kernel USB window is 30 s (`rubyusb_window_ms=30000`); the command channel
  accepts one text line per request (`help`, `stat`, `ring`, `echo`).

### Host side [measured]

- Windows 11 (`10.0.26300`, x64) on an AMD USB4 host.
- AMD USB 3.10 xHCI controllers; the USB 2.0 path used `1022:15b9`. The
  phone has been exercised on two physical setups:
  - the USB4 Type-C port with a C-to-C (CC) cable, and
  - a USB-A port with an A-to-C (AC) cable.
- Both setups show the same first-session XACT. On the A-port/AC-cable
  setup three fresh boots delivered 13, 7 and 23 frames with one device
  drop; earlier runs on the CC/Type-C port (0142/0143) delivered 2, 3, 9,
  15, 27 and 54 frames across boots. The samples are small: this is
  evidence that the cable/port is **not the sole cause**, not a claim that
  both links are equivalent.
- The phone is powered from the host port; no separate AC charger/adapter
  is attached in these tests. A charger + data setup is not covered.
- Host software: Python 3.x with `pyusb` + `libusb-package` (WinUSB
  backend). EP0 control requests use a 3 s timeout; EP2 reads poll at
  200 ms; normal sessions pace reads at 5 ms; burst reproduction sets
  pacing to 0.

## Driver binding [measured] / [inferred]

The device is vendor-specific class `0xFF`; it is expected to be bound to
WinUSB and opened through libusb. Do not bind a CDC/serial driver: if a COM
port appears for `1209:0002`, the wrong driver is bound and the host tool
will fail to open the device.

Generic binding steps (tool names are examples, not shipped here):

1. Install WinUSB for `1209:0002` (for example with Zadig: Options ->
   List All Devices -> select `ruby USB P2` (1209:0002) -> WinUSB ->
   Replace Driver).
2. Replug the phone and verify with
   `python tools/host/ruby_usb_host.py status`.
3. If a previous serial/CDC binding exists, remove that COM device first;
   do not install an unrelated CDC INF just to "make it appear".

Notes:

- `pnputil /enum-devices /connected` output is localized. Match the
  `VID_1209&PID_0002` line; do not parse English field names.
- Instance IDs are location-based; phantom entries remain after reboots.
  Match the present instance, not a hard-coded serial or location.
- No INF or driver binary is shipped by this repository.
- `pnputil /restart-device` works only while the device is still
  enumerated (admin required). It may re-enumerate and allow a new session,
  or it may drop the device. It is not a recovery for `NO_DEVICE`.

## Safe host debugging (do / do not) [measured]

**Do**

- Run one host tool at a time. EP2 OUT is a single command channel and the
  IN reader expects a quiet bus.
- Keep EP0 timeouts at 3 s and retry with backoff. EP0 is session-noisy:
  a first read can succeed, later reads in the same session can EPIPE;
  reconnecting is normal.
- Read EP2 with a 512-byte buffer; validate the 16-byte header and the
  sequence number. Normal 0143 frames are 511 bytes; a shorter final frame
  is legal.
- Use paced reads (5 ms) for long logs; use burst (`--pace-ms 0`) only
  when reproducing the XACT.
- On EPIPE/XACT, stop the IN reader and keep EP0 for diagnostics. A single
  `clear_halt(0x02)` after `claim_interface(0)` can recover a halted OUT
  pipe; do it once, not in a loop.
- If the device disappears (`NO_DEVICE`), stop and power-cycle the phone.
- For port/cable A/B, run several fresh boots per arm; a single session is
  not a stability measurement.

**Do not**

- Do not call clear_halt in a tight loop, and do not clear EP2 IN
  repeatedly. Both were measured to knock the device off the bus.
- Do not run `pnputil /restart-device` in a loop; once the device is gone
  it cannot help.
- Do not send commands while an IN drain is active; do not write EP2 from
  two processes.
- Do not hammer EP0 with back-to-back requests; EP0 noise is normal and
  retries only make it worse.
- Do not read arbitrary MMIO through 0x2C. It is whitelist-only (see
  below); an address outside the mappings returns STALL. Never scan the
  MTU3 FIFO0 window (`0x11201300`) or other data ports: a read can pop
  endpoint data.
- Do not treat the `0x22` `inflight`/`enq`/`deq` fields as full counts;
  they are 4-bit truncations. Use `outstanding = push_seq - txdone`.
- Do not attribute the XACT to one cable or port without repeated boots;
  both the CC and AC setups show it.
- Do not hot-plug an AC charger into the data port during a session; that
  combination is not tested here.

## Host tool reference

The stable reference tool is published at
[`tools/host/ruby_usb_host.py`](../../tools/host/ruby_usb_host.py); see
[`tools/host/README.md`](../../tools/host/README.md) for requirements and
output notes. It is read-only over EP0; the only device writes are the
EP2 OUT command text and the optional one-shot `--pcycle` restart.

```sh
python tools/host/ruby_usb_host.py status
python tools/host/ruby_usb_host.py cmd "help" --drain-secs 3
python tools/host/ruby_usb_host.py cmd "help" --drain-secs 3 --pace-ms 0
python tools/host/ruby_usb_host.py watch --pace-ms 5 --log session.log
```

- `status` reads `0x27` (EP0 counters), `0x23` (RX diagnostics), `0x2B`
  (log length) and `EP_RST`/`TX2CSR0`/`TQCSR2`/`TQCPR2`.
- `cmd` writes one line to EP2 OUT and drains EP2 IN for the requested
  time; the device answers with log/command frames.
- `watch` keeps a paced session; on EPIPE the IN reader stops but EP0
  stays usable; it reconnects with backoff when the device re-appears.
- `--pcycle` makes at most one `pnputil /restart-device` attempt for a
  wedged but still enumerated device. It needs an elevated shell; treat it
  as a last resort.

## Protocol details [measured]

### EP0 vendor requests

| Request | Direction | Purpose |
|---|---|---|
| `0xC0/0x21` | IN | State: `push_seq`, enq nibble, TX busy/ready, stall bits, `TQCSR2`, `TX2CSR0`, QISAR/TQERR |
| `0xC0/0x22` | IN | Queue diag: `txcpr`, HWO count, `inflight`/`enq`/`deq` nibbles, `txdone`, recoveries, QISAR0 |
| `0xC0/0x23` | IN | RX diag: packets, bytes, ZLP, last length, CRC/errors, RQ CSRs |
| `0xC0/0x27` | IN | EP0 counters: setups, tx packets, data ends, sent stalls, bus resets, cfg/ready |
| `0xC0/0x2A` | IN | Read a log window at a byte offset |
| `0xC0/0x2B` | IN | Log total bytes (64-bit) |
| `0xC0/0x2C` | IN | Read one 32-bit MMIO word (whitelisted mappings only) |
| `0x40/0x2D` | OUT | Write one 32-bit MMIO word; requires `rubyprobe=1`; **not used by the reference tool** |

### Frame and ring

- One frame = 16-byte header + up to 495 bytes of text = 511 bytes.
- Header sequence number is a 16-bit value at offset 0; text starts at 16.
- The slot stride is 512 bytes; a 512-byte slot never crosses a 16 KiB
  page, and the 64-byte GPD descriptor never crosses a 64-byte cache line.
  The TX ring holds 64 GPDs with at most 63 in flight.
- Each GPD is a short packet, which is what lets the QMU report TX done.
  A full 512-byte packet is not the same thing and was rejected in earlier
  experiments.

### `0x22` packing

`v[2]` packs: `hiar[3:0]`, HWO count `[15:8]`, `inflight[3:0]` at bit 16,
`enq[3:0]` at bit 20, `deq[3:0]` at bit 24. `v[3]` is `txdone`, `v[4]`
recoveries, `v[5]` QISAR0. The kernel uses 4-bit fields, so the host must
derive `outstanding = push_seq - txdone`; the published tool prints both
the nibbles and the derived value.

### `0x2C` readable ranges

| Mapping | Range | Notes |
|---|---|---|
| IFRAO | `0x10001000`-`0x10001fff` | clock-gate status; read-only use |
| GPIO | `0x10005000`-`0x10005fff` | pin mux/dir/out |
| MTU3 | `0x11201000`-`0x11203fff` | MAC; **FIFO0 `0x11201300` must not be read** |
| IPPC | `0x11203e00`-`0x11203eff` | inside the MTU3 mapping |
| PHY | `0x11e40000`-`0x11e41fff` | U2/U3 SIF; driver maps 0x2000 |

An address outside these ranges returns STALL; it does not fault. APMIXED
and topckgen (USB PLL/clock) are **not** mapped in 0143, so they cannot be
read with `0x2C` until a kernel mapping is added.

### The open failure [measured]

- First session: one command (`help`), then a variable number of 511-byte
  frames (0-54 observed; 0 means the IN pipe was already halted), then an
  IN URB completion `0xC0000011` (`USBD_STATUS_XACT_ERROR`) and
  `ABORT_PIPE`.
- At the abort the device-side QMU is active and the ring is full (63
  outstanding, `hwo=63`); QISAR0/TQERRIR0 are zero. It is not an empty-ring
  or a corrupt-packet symptom.
- EP0 may also XACT during enumeration and after the abort; Windows may
  issue `SYNC_RESET_PIPE_AND_CLEAR_STALL` and the device may drop. The
  root cause is still open; the 0143 kernel does not fix it.

## Evidence and limits

- Build: CI `41022192026`; patchset `f47f4c19...` (139 files); kernel full
  `d2eae74d...`, exec-data `6fa65088...`; image `5b6b8411...`
  (`config/0143.env`).
- Device runs: 2026-10-30, author's host, CC and AC setups; small samples.
- No logs, images or device identifiers are published. The numbers above
  are measured on the named builds; a new build must re-measure.
- A hardware USB analyzer/scope is the only way to observe bus-level CRC
  or 480 MHz jitter; `0x2C` register reads cannot prove or disprove it.
