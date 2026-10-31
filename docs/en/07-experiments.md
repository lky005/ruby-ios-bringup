# 07 — Experiments, failures and decisions

**English** · [中文](../zh/07-experiments.md)

The useful part of this project is not only what worked, but which hypotheses
were killed and why. This chapter is the shortest path to not repeating the
wrong turns.

## Timeline

| Date | Stage | Change | Result |
|---|---|---|---|
| 10-19 | Full image | stock/Magisk 128 MiB + red-screen payload | LK jumps, panel red |
| 10-19 | Probe 2–6 | console at `0x7cdfc000`, WDT off, 8 cores, GIC/timer | screen visible; 8/8 CPUs |
| 10-19 | Loader smoke | payload behind `_end`, jump `0x1_40000000` | green bar; boot_args/MMU path works |
| 10-19 | XNU | 1 core, then 8 cores; UFS read-only | `8/8 CPUs initialized`; UFS reads OK |
| 10-19 | UFS root | LUN 2, GPT header 512/entries 1024 | `BSD root: ufsroot0` |
| 10-20 | Layout | shrink userdata, create `iosroot` | Android data intact |
| 10-20 | Display | surface→panel, VA dcache flush | markers and live UI |
| 10-20 | Userland | pulled v14 root + seed; cache/cpus/ADT attempts | stacks unchanged |
| 10-20 | Kernel stub | 0082 `IONetworkController` | service published; notification not consumed |
| 10-20 | Timeout patch | `mov x1,#-1`→`#0` | lsd crash-loop; reverted |
| 10-21 | Trace | 0083 `SWEET IOX:` | `sent=1`; kernel was clean |
| 10-21 | ICL NOP | 4-byte `bl`→`nop` | boot22 lock screen 58 s |
| 10-21 | Autoswipe | 0084 kernel timer | boot23 warm 22 s from the Apple logo, home screen, animations |
| 10-22 | Real touch | 0085 Goodix SPI bit-bang, LDO VOUT 1.8/3.3 V | real bottom-edge unlock, two-contact HID dispatch, edge |
| 11-01 | Toolchain | build moved to a hosted `macos-15` image with Xcode 16.0; source unchanged | CI green; the interface-compiler step still generates cleanly |
| 11-01 | Enumeration | 0145 widens the attach window from 4 s to 12 s and raises the attempt budget | the host configures the device on the first try |
| 11-01 | Board probe | 0144 read-only probe commands over the USB console | 17 of 19 commands returned board data; the two pwrap reads stay empty |

## Failure catalogue

| Symptom | Likely cause | Check | Status |
|---|---|---|---|
| LK `hdr_loaded` on slot b | b-slot header/AVB path broken | same image on a works | use `_a`; abandoned b |
| `fastboot boot` fails | LK has no `boot:` | LK command table | flash `boot_a` |
| Screen invisible | console at `0x7ba10000` | LK scan layer is `0x7cdfc000` | use `0x7cdfc000`, stride 4352 |
| XNU hangs after `initCPU` | GIC/timer not prepared | shim GIC setup, 1 core first | prepare GIC, feed WDT |
| UFS root not found | wrong LUN/GPT offset | LUN 2, header 512, entries 1024 | patch 0080 |
| HFS+ mount fails | `userdata` is F2FS | partition type | use HFS+ `iosroot` |
| lsd stuck in MG wait | userland consumer, not kernel | `sent=1`, t5 loop | ICL NOP |
| lsd crash-loop after timeout patch | changed caller assumption | `CRASH lsd ns 2 code 0xa` | revert; wrong layer |
| ADT Wi-Fi node alone insufficient | device-tree plane ≠ IOService | trace still registers `IONetworkController` | not enough |
| Kernel stub published, still stuck | notification not consumed | 0083 trace | ICL NOP |
| Black wallpaper | PosterBoard first-time config | crash stack | open |
| Widgets `Waiting...` | WidgetKit/chronod/extensions | open | open |
| Date Dec 31 | no RTC/NTP | clock advances? | open |
| Original ICL block untested | NOP is a bypass | restore and boot | open |
| Goodix `CONF`/`VER` all zero | LDO VOUT left at PMIC defaults 3.0 V/1.8 V; only enable written | read LDO3 `0x09`, LDO2 `0x15` | write `0x3a`/`0xd0` |
| Controller read all zero after a write | 3 leftover FIFO bytes shift the read prefix | FIFO push count / `SPI_CMD_RST` | bit-bang; controller needs reset or DMA |
| Probe panic `0x96000021` | LLVM emitted an unaligned SIMD load with the MMU off | disassemble; FAR points into the stack | no-vectorize + volatile reads |
| `VER CS ok=1` on all-zero data | the checksum of zeros is zero | check non-zero data and `BERLIN` | reject all-zero |

## Decision records

**D1 — Full 128 MiB image.** A 36.7 MB image leaves a mismatched AVB footer;
LK fails at `hdr_loaded`. Keep DTB/AVB0/footer at stock offsets.

**D2 — `boot_a` only.** LK has no `boot:` and slot b is broken. Every
experiment is flashed to `boot_a`, with a known-good full image for rollback.

**D3 — Lossless layout is an appendix.** It avoids the initial Android erase
but edits the GPT and uses raw `dd`; not the default, not automated.

**D4 — ICL NOP over more kernel stubs.** Kernel delivery was already proven;
the consumer was the wall. The NOP is the smallest reversible bypass.

**D5 — Kernel autoswipe over userland injection.** The root has no shell/log
tools; a userland HID injector needs signing/entitlements. The kernel timer
reuses the existing `touch()`.

**D6 — `cpus=6` (A55).** 16K pages on A55 avoid the topaz Silver-core
workaround. A76 is not used yet.

**D7 — TWRP in `boot_a`.** There is no recovery partition and no `boot:`;
offline raw I/O requires flashing TWRP to `boot_a`.

**D8 — No firmware/diff data in the repo.** Images, iOS root, device dumps and
block diffs are not distributable and may contain personal data.

**D9 — Bit-bang SPI before the controller.** The controller path mixed FIFO,
pad-select and CS behavior; the bit-bang probe removed those variables and
proved the chip. Revisit the controller (DMA or FIFO reset) for rate/IRQ later.

**D10 — Write LDO VOUT, not just enable.** LK/PMIC defaults are VMC 3.0 V and
VTP 1.8 V; enabling without writing VOUT leaves AVDD undervolted and the chip
silent. Read the old VOUT, power-cycle, write 1.8 V/3.3 V, read back.


**D11 — One write per session.** The EP2 OUT channel only survives about
twenty writes per session, and the kernel parses the OUT buffer line by
line, so the whole command set goes out in a single write. A device stall
halts the EP0 IN endpoint for that handle only; reopen the handle and read
behind the write cursor. There is no hot-plug recovery: a halted endpoint
needs a physical power cycle.
## Do not repeat

- Do not question kernel notification delivery without a `sent=1` trace.
- Do not use the semaphore timeout patch; it only moves the crash.
- Do not add an ADT node and call it a service.
- Do not blame CPU count or launchd cache for the LS deadlock.
- Do not upgrade XNU expecting an IOKit fix; 8796 and 10063 are identical there.
- Do not assume the MG cache exists; it does not.
- Do not blame the panel for a black wallpaper.
- Do not use slot b or `fastboot boot`.
- Do not put firmware, dumps, serials or diff data in the repo.
