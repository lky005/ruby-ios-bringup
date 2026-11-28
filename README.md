# ruby-ios-bringup

**English** · [中文](README.zh.md)

[![xnu-0360](https://github.com/lky005/ruby-ios-bringup/actions/workflows/xnu.yml/badge.svg?branch=main)](https://github.com/lky005/ruby-ios-bringup/actions/workflows/xnu.yml)
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

Current line: 0360 (`v0.11.0`). It keeps the 0352 probe line and adds the
RubyGPU kernel driver recovered from the GPU lab line: the RubyGPU service
(device, power, MMU, BO, submit, context), its userclient UAPI (a Panfrost
kmod surface subset), the INTID487 IRQ, SG-backed BO allocation, per-task
surface ownership, the empty `IOAcceleratorES` service for Metal plugin
loading, selector-8 diagnostics (off by default), a 60 Hz SweetFB default with
a driver commit hook, and the CPU B4a AMP face (two clusters, Edge default
placement, read-only clock probe). The AMP face needs a 2-cluster ADT to take
effect; no ADT is shipped here, and the A78 cluster stays at 650 MHz (no
DVFS). The 0360 kernel is CI-verified only - it has not been booted on the
device. The 0352 line (`v0.10.0`) adds the read-only GPU probe and the gated
MFG2-5 power path (`rubygpupwr=2`, off by default).

| Pin | Value |
|---|---|
| Patchset | `bd125daf` — 327 files, gated in CI (0352 line: `40f7cefa`, 318) |
| Kernel | exec-data `4fef9a18` (record `46139168754`; gate `46140206357`); 0352 `90326b5e` (`46137921273`); full hashes in VERIFICATION |
| Device image | n/a — the 0360 kernel has not been booted; the lab image `7aa6e679` is not shipped |
| Tags | `v0.11.0` (0360) / `v0.10.0` (0352) |

| Subsystem | State | Notes |
|---|---|---|
| CPU and timers | Verified | 6× Cortex-A55 in one SMP cluster, 16 KiB pages, GICv3; the kernel also carries the CPU B4a AMP face (E/P buckets, Edge default placement), which needs a 2-cluster ADT - not shipped - to take effect |
| Storage | Verified | UFS LUN 2, read/write HFS+ root (`iosroot`); 4 MiB `md0` rescue ramdisk |
| Display | Verified | 1080×2400 panel through IOSurface/IOMFB; native backlight slider over DSI DCS `0x51` (v1.2 user-verified; v1.3 curve console-verified only); SweetFB defaults to 60 Hz on the 0360 line |
| Touch | Verified | Goodix GT9916R over SPI3 with a native EINT14 interrupt |
| Physical keys | Verified | Volume and power keys through KPD/TOPSTATUS and HID |
| First boot | Verified | Lock screen to home screen; staged apps and widgets render |
| USB device mode | Verified | EP0 command channel, MS OS 1.0 WinUSB binding, CDC-ECM NIC (macOS/Linux native; Windows via usbipd-win + WSL2) with SSH; 64 MB wget at 14.1 MB/s, TXRESET 0 on the 0349 run |
| GPU | Experimental | RubyGPU driver and PanVK/Mesa stack on the lab line: P3.4 native display and P3.5 GL verified on the device; the Metal-on-Vulkan shim stays research (composition WIP). The 0360 kernel is CI-verified only, never booted. See [15-gpu](docs/en/15-gpu.md) |
| Battery and Type-C | Read-only | MT6360 voltage and status telemetry at 1 s; unplug clears the full latch; no charging control |
| Wi-Fi, Bluetooth, cellular | Not implemented | connsys stub only |
| Audio, camera | Not implemented | — |
| Sleep, RTC, USB host | Not implemented | — |

Status is measured on a single unit; see
[GUARANTEE](docs/records/GUARANTEE.md). Known limits: backlight v1.3 hand feel
and Night Shift recovery were not user-accepted; the battery touch-lag A/B
(`rubybattms=5000`) was not run; host-side USB data is measured only on the
`0x81` channel; concurrent multi-endpoint traffic and RX on non-default
endpoints are not measured; `scp` pull can hit the FIFOFULL half-fetch window,
so large transfers go over HTTP. GPU claims are lab-line claims: no frame
rate, composition correctness or packaging guarantee is made, and the 0360
kernel has no boot record.

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
   device stack, the board HAL (keys, battery, pwrap) and, on the 0352+ lines,
   the RubyGPU driver face and the CPU B4a AMP face. The set is content-pinned
   and hash-gated.
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
python3 scripts/verify-local.py --ci-config config/0360.env

# 3. Reproduce the kernel
#    The xnu-0360 workflow builds from the pinned baseline and gates the
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
| GPU (15) | Kernel driver face, Mesa/PanVK line, Metal-shim research, gates |
| Records | [STATUS](docs/records/STATUS.md) · [VERIFICATION](docs/records/VERIFICATION.md) · [GUARANTEE](docs/records/GUARANTEE.md) |

```text
patches/   XNU delta: UFS, touch, keys, battery, USB/ECM, GPU driver face
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