# 06 — Input: Goodix touch, keys and autoswipe

**English** · [中文](../zh/06-input.md)

The current 0179 line drives the real Goodix GT9916R from the EINT14 hardware
edge through a child EINT controller and a dedicated IOWorkLoop oneshot. The
0085 bit-bang/polling path is kept below as history; the 0084 synthetic
autoswipe remains a fallback and a proof of the HID path. The detailed
hardware/protocol manual is [touch-goodix-9916r.md](touch-goodix-9916r.md).

## Native IRQ touch (0175–0179)

```text
EINT14 (edge falling)
  -> EINT child controller (vector = line)
       -> child IOInterruptEventSource on a dedicated IOWorkLoop
            -> gt_service_frame(): SPI3 read + HID submit
            -> service_done(): MASK_CLR + ACTIVE, re-arm the pin
```

- The SPI288 parent is level and is attached as RubyGIC INTID 288. Its filter
  only masks/acks/counts and raises line 14; it never sleeps or does SPI/HID.
- The child action runs in the work loop, not in the CPU interrupt. Commands
  and diagnostics are serialized on the same `IOCommandGate`; there is no
  `gt_thread` and no second SPI3 consumer.
- A dirty or failed frame is dropped and the line is re-armed unconditionally;
  it does not go STUCK/POLL_ONLY on one read error. Eight consecutive failures
  run one SPI FIFO reset and a chip soft handshake. The observed injected runs
  logged `soft reset no-ack` (the injector leaves 1–2 fail credits at the
  streak boundary), so the `ok` path is not proven.
- There is no ESD timer: a silent stuck panel with no new edge needs a reboot.
- Evidence: G1–G6; first 10 min `isr 2381→6004`, `ok=5997`, `fail=7`; ~5 min
  stress `isr 8672→13282`, `ok=12866`, `fail +9`; 1–5-finger frames; no panic,
  stuck or `line=14 active` re-activation. G7 (0177 rollback) and G8 (USB
  re-plug) were cancelled by decision.

## Real touch (0085, historical)

```
kernel thread (100 Hz poll)
  -> GT9916R frame at 0x10308 (34 bytes on the wire, 26 bytes of data)
  -> head + point checksum, sync clear
  -> sweet_hid_touch(id, down, raw_x/10, raw_y/10)
  -> IOHIDEventService -> backboardd -> SpringBoard
```

The driver:

- sets MT6360 LDO3 (VMC) to 1.8 V and LDO2 (VTP) to 3.3 V, enables them, and
  drives the IOVDD switch GPIO110 high; the LK/PMIC defaults are 3.0 V/1.8 V,
  so writing only the enable bits is not enough;
- pulses reset GPIO15 low 10 ms / high 100 ms;
- switches SPI3 pins 160-163 to GPIO and bit-bangs Mode 0 at ~250 kHz;
- verifies `dev_confirm` (8×0xAA at `0x10000`) and the `0x10014` version
  (`BERLIN`, PID `9916R`, U8-LE checksum) before reporting;
- polls `0x10308`, validates the 8-byte head and point checksums, writes 0 to
  clear sync, and reports up to two fingers; raw coordinates are divided by 10
  (10800×24000 -> 1080×2400) with no axis flip;
- releases a finger when it disappears or after 50 consecutive bad reads.

Live evidence: `SWEET GT: BERLIN/9916R ready, 1080x2400`; 206 down / 206 up
touch records, 40 finger-1 and 84 edge records; a real bottom-edge swipe
unlocked the lock screen. `SweetHIDTouch::touch()` appends both active fingers
to one digitizer collection when both are down; a user-visible pinch was not
separately instrumented. 0085 limits: polling, no IRQ/ESD, at most two
fingers, no firmware/config download. The 0179 line replaces the poll with
EINT14 (above); current runs logged 1–5-finger frames and reached 1–5 fingers
in HID.

## HID path

```
SweetHIDTouch::touch()
  -> IOHIDEventService -> IOHIDEventSystem
  -> backboardd -> SpringBoard
```

The real driver and the synthetic timer share this entry. `touch()` expects
panel pixels (0..1079 × 0..2399); `raw/10` is the correct mapping.

## Keys (0150 poll; 0169/0175 IRQ)

The 0150 driver polls the MTK KPD and the MT6359 `TOPSTATUS` register (kept
as history; 0169 added the volume-down KPD IRQ and 0175 moved it to RubyGIC
INTID 138):

- volume down: KPD `KP_MEM1` bit0 (0 = down);
- power: `TOPSTATUS 0x2a` bit1; volume up: bit3 (active-low, debounced);
- 20 ms poll with a two-sample confirm; `sweet_hid_key(0/1/2)` -> HID
  `0xe9`/`0xea`/`0x30`;
- zero PMIC writes; `0x910` stays `0x0025`. The 0155 device run exercised the
  keys in the 19-step probe;
- volume-down+power is parked; long-power and volume-up+power work.

In 0155 the touch LDO section takes the shared I2C5 IOLock used by the
battery and probe; `sweetgt=1` re-enables the 0085 driver. The 0179 runs used
the IRQ path (`rubyeint=1`, `rubyeintb1=1`, `rubykpdirq=1`) and exercised the
volume-down key in G4/G6 (G4 19 down/20 up; G6 43/43). The P2 diagnostic
images used `sweetgt=0` where noted.

## Edge tip

| Item | Value | Note |
|---|---|---|
| Start Y | `2390` | inside the bottom 48 px edge zone |
| Zone check | `y > 2399 - 48` | sets `kIOHIDDigitizerEventFromEdgeTip` |
| Why | UIKit requires the edge bit for the home gesture | otherwise the swipe is just a drag |

0071 added the edge-tip bit. The 0084 autoswipe starts at y=2390; real
bottom-edge swipes also carry the bit.

## Autoswipe (0084, retained)

| Argument | Meaning | 0084 value |
|---|---|---|
| `sweetautoswipe` | first delay in ms; 0 disables | `90000` |
| `sweetautoswiperetry` | retry interval in ms (min 1000) | `15000` |
| `sweetautoswipeattempts` | attempts (max 8) | `3` |

The 0085 boot cmdline omits these arguments and uses `sweetgt=1`. Set
`sweetgt=0` to disable the Goodix driver without rebuilding.

## Userland constraint

The current iOS root has no `/bin/sh`, `/usr/bin/log`, `launchctl` or
`notifyutil`; `hidutil` only reads/sets HID properties. The kernel driver was
therefore the smaller path.
