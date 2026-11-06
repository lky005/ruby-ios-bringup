# Goodix GT9916R touch manual

**English** · [中文](../zh/touch-goodix-9916r.md)

Hardware contract, power/protocol details, the bare-metal probe results, the
XNU driver, failure paths and reproduction steps for the Goodix GT9916R on
`ruby` / MT6877. Device serials, personal paths and full logs are not in this
repository. Evidence is marked measured/inferred where it matters.

## 1. Identity and contract

| Item | Value | Evidence |
|---|---|---|
| Panel | `m16_36_02_0b`, 1080×2400 | `/proc/cmdline` |
| TP variant | **TM** (not GVO) | Android dmesg |
| IC | Goodix **GT9916R**, BerlinD | dmesg |
| ROM / patch PID | `BERLIN` / `9916R` | read from `0x10014` |
| VID / sensor | `00 80 02 64` / `255` | dmesg and `0x10014` |
| Firmware | `goodix_firmware_m16_TM.bin`, 223,744 B, SHA-256 `4a3baefe…379424d7` | vendor firmware |
| Config | `goodix_cfg_group_m16_TM.bin`, 1,421 B, SHA-256 `8974708b…750121db` | vendor firmware |
| Input | ABS 10800×24000, 10 slots | `/dev/input/event5` |
| Host download | none when version/config match | vendor `goodix_fw_update_proc()` |

The firmware/config content is not in the repository; only names and hashes.

## 2. Wiring

| Signal | MT6877 | Note |
|---|---|---|
| SPI3 | `0x11013000` | `mediatek,mt6765-spi`, CS0, Mode 0, 8-bit |
| SPI pins | GPIO **160/161/162/163** | MO / MI / CSB / CLK, function 2 |
| IRQ | GPIO14, EINT14 | falling edge; v1 polls instead |
| Reset | GPIO15 | active low; low 10 ms, high 100 ms |
| IOVDD switch | GPIO110 | high=on, `ts_dvddenable` |
| AVDD | MT6360 **LDO2 / VTP** | 3.3 V; EN `0x11` bit6, VOUT `0x15` |
| IOVDD | MT6360 **LDO3 / VMC** | 1.8 V; EN `0x05` bit6, VOUT `0x09` |
| I2C5 | `0x11d00000`, slave `0x64` | SCL GPIO132, SDA GPIO133 |

The `ts_spimode` raw values are `0xa002/0xa102/0xa202/0xa302`: the high byte
`0xA0..0xA3` is GPIO 160..163 and the low byte `2` is function 2.

## 3. Power and reset

### 3.1 MT6360 LDO CRC8 access

The LDO registers use a **CRC8-protected SMBus block**:

- write: `START, addr<<1, reg&0x3f, value, crc, dummy0, STOP`;
- read: `START, addr<<1, reg, repeated START, addr<<1|1, value+ACK, crc+NACK, STOP`;
- CRC8: poly `0x07`, init `0`, MSB-first over `[addr<<1, reg&0x3f, value]`;
  the read direction uses `addr<<1|1`.

Abort on a CRC mismatch; never write after a failed read.

### 3.2 The default-voltage trap

Android's early dmesg:

```
vtp: Bringing 1800000uV into 3300000-3300000uV
VMC: Bringing 3000000uV into 1800000-1800000uV
```

LK/PMIC leave **VMC at 3.0 V and VTP at 1.8 V**; Android changes them to
1.8 V/3.3 V. Enabling the rails without writing VOUT leaves AVDD undervolted
and the chip never boots. This was the root cause of the all-zero P1f/P1g
reads. The driver writes:

- LDO3 `0x09 = 0x3a` (selector `0x3a..0x40` = 1.8 V);
- LDO2 `0x15 = 0xd0` (selector `0xd0..0xd9` = 3.3 V).

P1f/P1g enabled the rails before VOUT was written, so the chip briefly saw
VMC at 3.0 V before the fix; it survived. Do not repeat that deliberately:
write VOUT while the rails are disabled, read it back, then enable.

### 3.3 Power-up order

```
read EN/VOUT (CRC8)
disable LDO3/LDO2 (clear bit6) -> 20 ms
write VOUT 0x3a/0xd0, read back
IOVDD GPIO110 high -> 3 ms
enable LDO3 -> 30 ms
enable LDO2 -> 15 ms
SPI pins to GPIO, idle CS high / CLK low
reset15 low 10 ms -> high 100 ms
dev_confirm -> version -> poll
```

After enable, the EN register typically changes from `0x80` to `0xC4`
(bit6=1). Bit2 is a read-only status; preserve it in RMW writes.

## 4. Pinmux / GPIO registers

MTK pinctrl uses two numbering schemes:

- **DIR/DO/DI** use 32-pin banks: bank `n` at
  `DIR=0x000+n*0x10`, `DO=0x100+n*0x10`, `DI=0x200+n*0x10`;
- **mode** uses 8-pin groups: `0x300+group*0x10`, 4 bits per pin.
  group = pin/8, not the bank number.

| Function | Pins | Bank | Mode | DIR/DO/DI |
|---|---|---|---|---|
| I2C5 SCL/SDA | 132/133 | 4 | `0x400` bits16–23 | `0x040/0x140/0x240` |
| SPI3 MO/MI/CS/CLK | 160–163 | 5 | `0x440` bits0–15 | `0x050/0x150/0x250` |
| Reset | 15 | 0 | `0x310` bits28–31 | `0x000/0x100/0x200` |
| IOVDD | 110 | 3 | `0x3d0` bits24–27 | `0x030/0x130/0x230` |

Bits: MO=0, MI=1, CS=2, CLK=3; SCL=4, SDA=5; reset=15; IOVDD=14.

Pitfalls:

- **`0x400/0x440` are group 16/20**, not bank 4/5;
- MTK clock gates are active-low: CLR `0x100010a8` bit10 opens, SET
  `0x100010a4` bit10 closes, and STA `0x100010ac` bit10=1 means gated. The
  bit-bang driver does not depend on the SPI3 controller clock;
- CPOL/CPHA live in `SPI_CMD` bits 8/9; `CFG0=0x3F003F` is CS setup/hold
  timing, not mode 3;
- I2C/SPI lines are open-drain with external pull-ups; release by setting DIR
  to input.

## 5. SPI protocol (BerlinD)

### 5.1 Frames

- Mode 0 (CPOL=0, CPHA=0), 8-bit, MSB first, CS active low;
- write prefix **5 bytes**: `0xF0 + addr(4, BE)` then data;
- read prefix **8 bytes**: `0xF1 + addr(4, BE) + 0xFF×3` then data;
  MOSI is 0 during the data phase;
- bit-bang half-period 2 µs (~250 kHz); the controller nominal rate is 5 MHz.

### 5.2 dev_confirm and version

- `dev_confirm`: write 8×`0xAA` at `0x10000`, read 8 bytes back; the vendor
  retries up to 3 times with 5 ms gaps.
- Version: read 28 bytes at `0x10014`:

| Offset | Field |
|---|---|
| 0–5 | ROM PID, `BERLIN` |
| 6–8 | ROM VID |
| 9 | reserved |
| 10–17 | patch PID, `9916R` |
| 18–21 | patch VID, `00 80 02 64` |
| 22 | reserved |
| 23 | sensor id, `0xFF` |
| 24–25 | reserved |
| 26–27 | U8-LE checksum |

Check: `sum(data[0..25]) & 0xffff == data[26] | data[27]<<8`.

### 5.3 Touch frame

Touch data is at `0x10308`. Pre-read 26 data bytes (34 on the wire):

| Offset | Meaning |
|---|---|
| 0 | event; `0x80` = `GOODIX_TOUCH_EVENT` |
| 1 | reserved |
| 2 | `touch_num = value & 0x0f` |
| 3–5 | reserved |
| 6–7 | head checksum: `sum(data[0..5]) & 0xffff` |
| 8–15 | point 0 |
| 16–23 | point 1 |
| 24–25 | point checksum for one point; 32–33 for two |

A point is 8 bytes: `[0]` high nibble id, low nibble type (1/3 = pen);
`[2..3]` x LE16; `[4..5]` y LE16; `[6..7]` w.
The point checksum covers `data[8 .. 8+n*8-1]`.

After a valid frame, write one 0 byte to `0x10308` to clear sync (6 bytes on
the wire). For `touch_num > 2`, the vendor reads extra bytes at
`0x10308+26`; v1 drops the frame and clears sync.

### 5.4 Controller FIFO trap

The MTK SPI controller has a 32-byte FIFO; the 34-byte pre-read needs DMA or
32+2 pause/resume. P1f pushed a 16-byte word-aligned FIFO payload for a
13-byte write, the controller shifted out 13 bytes, and **3 bytes remained**.
The next read then started with `00 00 00`, shifting the read prefix; the write
succeeded but reads were all zero. The vendor resets the FIFO (`SPI_CMD_RST`)
on CS deassert. A future controller path must flush the FIFO between transfers
or use DMA. The current XNU driver uses bit-bang and avoids this.

## 6. XNU driver (0085 poll; 0179 native EINT)

> The table below describes the historical 0085 polling driver. The current
> 0179 line keeps the same power/protocol code but services frames from the
> EINT14 hardware edge; see §6.1.



| Item | Value |
|---|---|
| File | `bsd/dev/sweet_goodix_spi.c` |
| Start | `sweet_ufs.c` calls `sweet_goodix_spi_init()` |
| Boot arg | `sweetgt=1` (default on), `sweetgt=0` off |
| Build | one line in `bsd/conf/files` |
| MMIO | `ml_io_map(0x10005000, 0x1000)` |
| Thread | `kernel_thread_start()`; exits on init failure |
| Poll | 34-byte read + sync clear, ~8 ms sleep -> ~100 Hz |
| Report | `sweet_hid_touch(id, down, raw/10, raw/10)` |
| Release | missing finger, `n=0` frame, or 50 consecutive bad reads |
| Limits | ≤2 fingers, no IRQ/ESD, no firmware download |

The power/protocol logic is the same as the bare-metal probe. XNU runs with
the MMU on, so the probe's Device-memory unaligned-access restriction no
longer applies.

### 6.1 Native EINT service (0179)

```text
EINT14 (edge falling)
  -> EINT child controller (vector = line)
       -> child IOInterruptEventSource on a dedicated IOWorkLoop
            -> gt_service_frame(): SPI3 read + HID submit
            -> service_done(): MASK_CLR + ACTIVE, re-arm the pin
```

- SPI288 parent is level and becomes RubyGIC INTID 288; its filter only
  masks/acks/counts and raises line 14.
- The child action owns SPI3/HID; commands and diagnostics run on the same
  `IOCommandGate`; `gt_thread` is removed and there is no second consumer.
- A failed frame is dropped and the line is re-armed. Eight consecutive
  failures run one SPI FIFO reset + chip soft handshake. Injected tests logged
  `soft reset no-ack` (the injector leaves 1–2 fail credits at the boundary),
  so the `ok` path is not proven.
- No ESD timer; a silent stuck panel needs a reboot.
- Evidence: G1–G6; first 10 min `isr 2381→6004`, `ok=5997`, `fail=7`; ~5 min
  stress `isr 8672→13282`, `ok=12866`, `fail +9`; no panic/stuck/re-activation.
  G7 (0177 rollback) and G8 (USB re-plug) were cancelled by decision.

## 7. Bring-up history (including wrong turns)

| Stage | Goal | Result |
|---|---|---|
| P0 | read-only registers | LK left IOVDD pin110 DO=0; SPI3 unconfigured; CG open |
| P1/P1b | controller PIO | wrote SET, actually gated the clock; all-zero was expected |
| P1c | CLR gate, mode 2 | SPI3 registers worked; Goodix still zero |
| P1d | IOVDD high | still zero; VMC unconfirmed |
| P1e | plain I2C | LDO read `0x80`, writes did not stick; wrong protocol |
| P1f | CRC8 block | LDO3/LDO2 0x80→0xC4; still zero |
| P1g | GPIO bit-bang SPI | link verified (CS→DI self-test); chip silent |
| Key find | Android dmesg | defaults VMC 3.0 V / VTP 1.8 V; VOUT never written |
| P1h | write VOUT | panic: LLVM SLP emitted `ldur s0,[x0,#2]`, alignment fault with MMU off |
| P1h2 | no vectorization + volatile | **BERLIN/9916R, CONF/VER passed** |
| P2 | 30 s frame poll | real touch frames, checksums, raw x/y valid |
| P3 | XNU driver | real bottom-edge unlock, two-contact HID dispatch, edge |

Lessons:

- `VER CS ok=1` is also true for all-zero data; reject all-zero explicitly;
- a probe with the MMU off can fault on compiler-generated unaligned wide
  accesses; `-mstrict-align` alone was not enough, so the probe uses
  `-fno-vectorize -fno-slp-vectorize` and volatile byte reads;
- TWRP log reads use `dd` + `adb pull` (the old adb has no `exec-out`); Git
  Bash needs `MSYS_NO_PATHCONV=1` for `/tmp` paths.

## 8. Debug checklist

1. I2C5 idle: SCL/SDA both 1; otherwise check pinmux/input enable.
2. Read LDO3/LDO2 EN/VOUT; expected old values are `0x80/0xB0`, `0x80/0x40`.
3. After writing VOUT, readback must be `0x3A/0xD0`; after enable, `0xC4`.
4. `dev_confirm` fails: check reset timing, IOVDD, SPI wiring.
5. Version fails: check `BERLIN`, checksum, sensor.
6. All-zero frames: check CS/CLK/MISO and sync clear; with the controller,
   fix the FIFO first.
7. Frames but no touch: check `event & 0x80`, `touch_num`, point checksum,
   `raw/10`, and the HID consumer.
8. Orientation: Android's Touch Mapper shows `YScale=0.100` and no inversion,
   so `raw/10` is used directly; if the device is upside down, apply
   `y = 2399 - y/10` in the driver.

## 9. Reproduction, CI and flashing

- Patch: `patches/0085-ruby-goodix-spi.patch`.
- Canonical patchset: `cf4008e3…c0a03f` (88 files; identical to the harness
  patchset that built the booted kernel).
- Build: `.github/workflows/xnu.yml` fetches the pinned baseline, applies the
  delta, runs `ci/prepare-baseline.sh`, and hashes the kernel segments with
  `ci/kernel_hash.py`.
- Booted kernel: `9eb9acac…`; exec-data `e4823afb…`; boot image `ace60d16…`.
- Cmdline: `config/0085-boot.cmdline` (`sweetgt=1`, no autoswipe).
- Flash only `boot_a`; keep the rollback and Magisk base outside the
  repository. Boundaries: no preloader/lk/persist/nvram writes, no UFS GPT
  changes. See `docs/records/SAFETY.md`.

## 10. Evidence

Sanitized sweetlog excerpt:

```
SWEET GT: LDO3 en=80 vout=b0, LDO2 en=80 vout=40
SWEET GT: rails on en3=c4 en2=c4
SWEET GT: BERLIN/9916R ready, 1080x2400
```

Touch statistics: 413 `SWEET HID: touch` records, 206 down / 206 up,
40 finger-1 and 84 edge records; down x 0–1038, y 5–2399; no
stopped/panic/fail. When two contacts are active, `SweetHIDTouch::touch()`
appends both finger children to one digitizer collection; a user-visible pinch
was not separately instrumented. The full log is external; only the excerpt and
aggregate counts are recorded.
