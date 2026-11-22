# ruby-ios-bringup

**English** · [中文](README.zh.md)

[![xnu-0351](https://github.com/lky005/ruby-ios-bringup/actions/workflows/xnu.yml/badge.svg?branch=main)](https://github.com/lky005/ruby-ios-bringup/actions/workflows/xnu.yml)
[![host-checks](https://github.com/lky005/ruby-ios-bringup/actions/workflows/host-checks.yml/badge.svg?branch=main)](https://github.com/lky005/ruby-ios-bringup/actions/workflows/host-checks.yml)

A research bring-up that ports Apple's open-source XNU 8796 kernel and an
iPhone X (iOS 16.7.16) userland to the MediaTek MT6877 platform
(Redmi Note 12 Pro 5G, `ruby`). The device keeps its stock bootloader chain;
`boot_b` holds TWRP as a recovery path.

The repository publishes the kernel delta, the build recipe, host-side tools
and the documentation. It contains no Apple firmware, IPSW files, root images
or device dumps; full hashes, run history and per-subsystem evidence live in
[STATUS](docs/records/STATUS.md) and
[VERIFICATION](docs/records/VERIFICATION.md).

## Status

Current line: 0351 (`v0.9.0`). It keeps the 0349 USB/ECM line and adds a
native display backlight (DCS `0x51` over the MT6877 DSI VM_CMD path, gamma
2.6 LUT with a preemptible ramp) and 1 s read-only battery polling. The
backlight is off unless `rubybacklight=1 rubyblhw=1`; the 0351 boot line
enables both. The v1.3 curve is console-verified only; hand feel and Night
Shift are not user-accepted.

| Pin | Value |
|---|---|
| Patchset | `bce06bba` — 316 files, gated in CI |
| Kernel | exec-data `9febbe97` (CI `45001473122`; gate rerun `45003136758`); full hash in VERIFICATION |
| Device image | `f0f7d454` (`x16-blv13.img`), 440 B boot line |
| Tags | `v0.9.0` / `p4-bl-batt-final` |

| Subsystem | State | Notes |
|---|---|---|
| CPU and timers | Verified | 6× Cortex-A55, 16 KiB pages, GICv3 |
| Storage | Verified | UFS LUN 2, read/write HFS+ root (`iosroot`); 4 MiB `md0` rescue ramdisk |
| Display | Verified | 1080×2400 panel through IOSurface/IOMFB; native backlight slider over DSI DCS `0x51` (v1.2 user-verified; v1.3 curve console-verified only) |
| Touch | Verified | Goodix GT9916R over SPI3 with a native EINT14 interrupt |
| Physical keys | Verified | Volume and power keys through KPD/TOPSTATUS and HID |
| First boot | Verified | Lock screen to home screen; staged apps and widgets render |
| USB device mode | Verified | EP0 command channel, MS OS 1.0 WinUSB binding, CDC-ECM NIC (macOS/Linux native; Windows via usbipd-win + WSL2) with SSH; 64 MB wget at 14.1 MB/s, TXRESET 0 on the 0349 run |
| Battery and Type-C | Read-only | MT6360 voltage and status telemetry at 1 s; unplug clears the full latch; no charging control |
| Wi-Fi, Bluetooth, cellular | Not implemented | connsys stub only |
| Audio, camera, GPU | Not implemented | — |
| Sleep, RTC, USB host | Not implemented | — |

Status is measured on a single unit; see
[GUARANTEE](docs/records/GUARANTEE.md). Known limits: backlight v1.3 hand feel
and Night Shift recovery were not user-accepted; the battery touch-lag A/B
(`rubybattms=5000`) was not run; host-side USB data is measured only on the
`0x81` channel; concurrent multi-endpoint traffic and RX on non-default
endpoints are not measured; `scp` pull can hit the FIFOFULL half-fetch window,
so large transfers go over HTTP.

## Architecture

```text
stock LK (boot_a)
  → boot image (kernel + ADT + shim)
  → XNU 8796 + MT6877 board HAL (UFS, display, IRQ, USB/ECM)
  → iOS 16.7.16 userland (SpringBoard)
```

1. Boot image — `src/bringup/` packs the kernel, ADT and shim into the
   128 MiB geometry stock LK expects; `boot_b` (TWRP) is the recovery path.
2. Kernel delta — `patches/` applies the MT6877 port onto `xnu-8796.141.3`:
   interrupt routing, UFS block I/O, Goodix SPI3/EINT touch, the MTU3 USB
   device stack and the board HAL (keys, battery, pwrap). The set is
   content-pinned and hash-gated.
3. First boot — `tools/image/` patches the LaunchServices deadlock at the
   dyld level (a 4-byte ICL NOP) and verifies root and boot-image integrity
   before flashing.

## Build and verify

Prerequisites:

- Host: macOS 13.5 or newer with Xcode 16.0 (the CI runner is `macos-15`);
  Python 3.10 or newer for host-side checks.
- Target: a bootloader-unlocked Redmi Note 12 Pro 5G (`ruby`) with TWRP on
  `boot_b`, and an iPhone X iOS 16.7.16 root built from your own IPSW.

```sh
# 1. Assemble the content-pinned baseline (private mirror; public fallback below)
sh ci/prepare-baseline.sh <dest>
ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>

# 2. Run the host-side checks (read-only, no device)
python3 scripts/verify-local.py --ci-config config/0351.env

# 3. Reproduce the kernel
#    The xnu-0351 workflow builds from the pinned baseline and gates the
#    patchset and exec-data hashes; it fails if a project patch is skipped.
```

The boot image itself is not included; `tools/image/` provides the offline
verifier and patch tools. Full recipe, image packing and flashing are in
[09-reproduce](docs/en/09-reproduce.md); recovery is in
[08-recovery](docs/en/08-recovery.md).

## Documentation

Start at the [docs index](docs/README.md)
([English](docs/en/README.md) · [中文](docs/zh/README.md)).

| Section | Contents |
|---|---|
| Architecture (01–07) | SoC, boot chain, display, userland, input, hardware notes |
| Build and CI (08–11) | Recovery, reproduce, scripts, baseline recipe |
| USB (12–14) | Host channel, EP2 golden path, per-endpoint queues |
| Records | [STATUS](docs/records/STATUS.md) · [VERIFICATION](docs/records/VERIFICATION.md) · [GUARANTEE](docs/records/GUARANTEE.md) |

```text
patches/   XNU delta: UFS, touch, keys, battery, USB/ECM
src/       boot-image packer, ARM64 shim, UFS probe
tools/     host USB tools, image verifiers, SWEETLOG decoder, TWRP diff
ci/        pinned baseline recipe, patchset pin, kernel hash gates
config/    per-line kernel and boot-argument configuration
docs/      bilingual guides and records
```

Per-run hardware logs and probe cards are kept in the separate
[`lky005/ruby-ios-probes`](https://github.com/lky005/ruby-ios-probes)
repository. Project history is in [STATUS](docs/records/STATUS.md) and
[07-experiments](docs/en/07-experiments.md); the 0084-era demo clip and photo
remain under `media/` with the capture rules in
[media/CAPTURE.md](media/CAPTURE.md).

## Safety and scope

Flashing an experimental boot image and repartitioning `iosroot` can erase
Android `userdata`. Treat data loss as expected, and read
[SAFETY](docs/records/SAFETY.md) and [SCOPE](docs/records/SCOPE.md) before
flashing. The dual-boot layout is a method note, not an installer. AMFI,
sandbox and code signing are disabled; treat the userland as unhardened.

The repository ships no Apple firmware and no personal data. Please do not
post or request proprietary files in issues; see
[CONTRIBUTING](.github/CONTRIBUTING.md).

## License

Original code and documentation are MIT-licensed. The patches modify Apple's
XNU and remain under APSL 2.0. Upstream projects and excluded material are
listed in [NOTICE](NOTICE), [ACKNOWLEDGEMENTS](docs/records/ACKNOWLEDGEMENTS.md)
and [LEGAL](docs/records/LEGAL.md).