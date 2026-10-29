# ruby-ios-bringup

**English** · [中文](README.zh.md)

**XNU 8796 + iPhone X iOS 16.7.16 userland on a MediaTek MT6877 phone.**
A research bring-up, packaged as an independent, sanitized delta.

> **Status 2026-10-29:** the kernel CI now assembles from a content-pinned
> 82-file baseline (manifest root `829d7598...`) fetched from a private
> content-addressed mirror; the 0001-0079 baseline is no longer a live upstream
> dependency. The ramdisk line adds the LK-ramdisk rescue root (`md0`, PID 1
> in-process, 8/8 rescue `/etc/rc` checks, USB `1209:0002` enumeration at ~35 s); the ramdisk and USB lines
> are combined on `main` (squashed from `merge-ramdisk-usb-2026-10-29`).
> `usb-0131b-probe-write` keeps the vendor USB probe; EP2 host-side XACT
> remains open. Real touch (0085) remains the last UI milestone; no new device
> image was flashed for this CI change.
>
> **Status 2026-10-22:** **real touch works.** The 0085 kernel drives the
> Goodix GT9916R over bit-bang SPI3, unlocks the lock screen with a real
> bottom-edge swipe, and dispatches two simultaneous contacts and edge events
> to the HID layer (kernel IOLog; a user-visible pinch was not separately
> instrumented). The 0084 image
> and a CI-built kernel also reach the lock screen and the synthetic swipe to
> the home screen. **Timings are measured from the Apple logo:** the B+NOP
> first boot was observed at 22 s to lock screen and 30 s to autoswipe; the
> historical first boot was ~58 s and the warm reboot ~22 s. Buttons, USB,
> Wi-Fi, GPU and RTC are still not implemented.
>
> **Device regression:** the B+NOP first boot -> A', the CI kernel boot, and
> the real-touch 0085 boot were run on the author's unit on 2026-10-22. A
> second unit/clean-room and the from-IPSW root/shim/ADT builders remain open.
> See [`GUARANTEE.md`](GUARANTEE.md).

## Demo

[<img src="media/home-screen.jpg" width="360" alt="SpringBoard home screen after the synthetic swipe">](media/autoswipe.mp4)

**Click the image to play the 12 s clip** (720p60, 2.6 MB): lock screen →
kernel-side synthetic swipe → home screen. Captured on the 0084 build on
2026-10-21; metadata and audio stripped. See
[`media/README.md`](media/README.md).

This repository contains **no Apple firmware, iOS root images, device dumps or
diff data**. The kernel is built from Apple's xnu tag, a content-pinned 82-file
baseline and this project's delta; the workflow verifies the applied tree
before building.

## At a glance

| Area | State |
|---|---|
| Boot | stock LK → 128 MiB boot image → XNU 8796 → HFS+ root (UFS, or `md0` rescue) |
| CPU | 6× Cortex-A55, 16K pages, GICv3, timers |
| Display | IOSurface/IOMFB → LK framebuffer, 1080×2400 |
| Userland | launchd → lsd → backboardd → SpringBoard |
| Input | **real Goodix GT9916R** over bit-bang SPI3; unlock, two-contact HID dispatch, edge; 0084 synthetic swipe still available |
| Storage | UFS LUN 2, read/write HFS+ on `iosroot`; 4 MB HFS rescue root via the LK ramdisk slot |
| Latest runs (separate) | 2026-10-29 rescue root (8/8 rescue `/etc/rc` checks); 0085 real-touch boot (harness and main-CI rebuild); 0084 B+NOP first boot -> A' (22 s / 30 s from the Apple logo) |
| Open | second unit/clean-room; from-IPSW root/shim/ADT builders; strict pinned payload; USB EP2 host-side XACT |
| Not yet | keys, Wi-Fi, GPU, RTC; USB is a probe only |
| Safety | AMFI/sandbox/code signing off; data may be lost |

## Why this milestone matters

The hard walls were not "boot XNU" but three silent failures: the 128 MiB image
layout LK accepts, the display path that actually reaches the panel, and a
LaunchServices first-boot deadlock that looked like a kernel bug but was a
userland `MobileGestalt` consumer. The repository records the exact bytes, the
evidence and the wrong turns.

## Repository map

| Path | Contents |
|---|---|
| `README.md`, `STATUS.md`, `SCOPE.md`, `SAFETY.md` | entry points and boundaries |
| `ACKNOWLEDGEMENTS.md`, `LEGAL.md` | credits and legal risk notice |
| `docs/en/`, `docs/zh/` | English and Chinese chapters |
| `touch/` | probe ladder, hardware contract and sanitized lab notes |
| `patches/` | own XNU delta: 0080 UFS, 0085 Goodix touch, 0086-0131b USB, 0140/0141 ramdisk; historical 0081-0084 |
| `ci/` | baseline manifest/recipe, canonical patchset hash, kernel segment hash and provenance |
| `config/` | 0140 ramdisk and 0131b USB pins; 0085 real-touch and 0084 as history |
| `.github/workflows/xnu.yml` | reproduces the current kernel and gates its patchset/exec-data hash |
| `src/bringup/` | early boot payloads, shim, image packers |
| `src/ufs-probe/` | read-only MT6877 UFS probe |
| `tools/image/` | ICL patch, dyld scanner, boot verifier |
| `tools/twrp/` | validated block diff/patch (TWRP) and host CRC/target helpers |
| `tools/sweetlog/` | SWEETLOG ring decoder |
| `scripts/` | baseline fetch, host verification |
| `media/` | sanitized demo clip, home-screen photo and capture rules |
| `ruby-ios-probes` | separate public probe/run-card repository (no Apple material) |

## Probe / test lab

Environment and device-test records live in a separate public repository:
[`ruby-ios-probes`](https://github.com/lky005/ruby-ios-probes).

Why separate:

- this repository is the stable recipe/contract (patches, CI, boot-image pins,
  hashes);
- the probe repository holds host/device checks, run cards and hash-stability
  notes, which change every run;
- separate CI keeps a failed environment probe from affecting the kernel build.

This repository remains the source of truth for the recipe and hashes; the
probe repository only records probes and tests. Neither contains Apple material.

## Build and verify

```sh
# host checks: no device, no image writes
python scripts/verify-local.py

# host-side diff/restore helpers (read-only on the source image)
python tools/twrp/make_crc_map.py <image> <map>
python tools/twrp/make_target_patch.py <image> <idx> <patch> --crc-map <map>

# SWEETLOG ring decoder (host)
python tools/sweetlog/decode.py <area.bin> <out.txt>
```

The kernel workflow uses:

```text
apple:    apple-oss-distributions/xnu @ xnu-8796.141.3 (f625db25...)
baseline: 82 files (sweet 0001-0079), manifest root 829d7598...
recipe:   ci/prepare-baseline.sh (private mirror; public fallback ALLOW_PUBLIC_UPSTREAM=1)
patchset: 27894e7b... (main, 137 files; USB branch 29449e32..., 135 files)
runner:   macos-14 / Xcode 15.0.1 / macOS 13.5 xnu
config:   DEVELOPMENT, MACHINE_CONFIG=SWEET, -mcpu=cortex-a55
```

The recipe verifies the 82-file baseline, adds this project's patches, applies
the small 0010/0012 change, normalizes line endings and refuses to build unless
the canonical patchset hash matches. See `docs/en/11-ci-baseline.md`. The boot image itself is **not** included;
`tools/image/` provides the offline verifier and patch tools.

Host pipeline (no device, no root): `scripts/test-pipeline.sh` with a base boot
image, kernel, ADT, shim and the golden 0084 image (the 0084 milestone harness;
the 0085 path uses the three commands in `docs/en/09-reproduce.md` with
`config/0085.env`). It builds the payload, packs a deterministic image and
checks the layout.

## Device situation

| Item | Value |
|---|---|
| Device | Redmi Note 12 Pro 5G, `ruby` / MT6877, 8 GB + 256 GB |
| System | Android 12 / MIUI 13.0.4, unlocked, Magisk, slot `_a` |
| Layout | `userdata` 208.4 GiB + `iosroot` 17 GiB; `boot_a` 128 MiB; `super` ~9.1 GB |
| Current state | artifacts: real-touch 0085 image/kernel, 0084 image, root A/A' snapshots, ICL blocks, boot cmdline; the device is not part of this repository |
| Success artifacts | 0085 image, kernel, root A/A' snapshots, ICL blocks, boot cmdline |
| Must match | firmware/GPT, root hash, boot image, boot args, panel/display |
| Not needed | touch firmware, Wi-Fi, USB, GPU, RTC |

Root states (external; pinned in `config/0085.env`):

| State | SHA-256 | Meaning |
|---|---|---|
| A success | `e698339d...` | post-boot22; ICL NOP + first-boot state |
| B pre-boot22 | `985c30...` | pulled+seeded; ICL original; the boot22 diff maps B -> A |
| C clean base | `34c2882d...` | mkiosroot + tweaks; first boot/seed needed |
| A' first boot | `55e2ab2c...` | one B+NOP first-boot snapshot; new first boots differ |

Device-baseline hashes (GPT/boot/vbmeta) are intentionally **not** published;
they can fingerprint the unit. Artifact hashes are in `config/0085.env`. See
[`docs/en/device.md`](docs/en/device.md) / [`docs/zh/device.md`](docs/zh/device.md).

## Scope and safety

- The default path writes an iOS root and can erase Android data. **Assume
  data loss.**
- The dual-boot layout is an appendix **method note**, not an installer.
- No Apple firmware, no activation against Apple servers, no personal data.
- Read [`SAFETY.md`](SAFETY.md) and [`SCOPE.md`](SCOPE.md) before flashing.
- Content policy: do not post or request Apple firmware, iOS root, dyld
  caches, device dumps, serials/IMEI/MAC or personal data. See the issue
  template (`.github/ISSUE_TEMPLATE/`) and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Guarantee

The success path — boot to the lock screen and the synthetic swipe to the home
screen — now has **one-unit device evidence** (B+NOP first boot -> A', and the
CI kernel boot) plus the documented recipe. It is not a second-unit or
clean-room guarantee. Pre-boot artifact hashes are fixed for the named files;
post-boot live-root/ring/log hashes are volatile. The from-IPSW root/shim/ADT
builders and the strict pinned payload rebuild are still open. See
[`GUARANTEE.md`](GUARANTEE.md).

## Docs

Start at [`docs/README.md`](docs/README.md), or go directly to the
[English chapters](docs/en/README.md) / [中文章节](docs/zh/README.md).

## Acknowledgements and legal

See [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md) and [`LEGAL.md`](LEGAL.md).
Media capture rules are in [`media/CAPTURE.md`](media/CAPTURE.md).

## License

Original code and documentation are MIT-licensed. The patches modify Apple's
XNU and remain under APSL 2.0. Upstream projects and excluded material are
listed in [`NOTICE`](NOTICE).

**Upstream note:** `ios-sweet` and `ios-topaz` had no license file at the
pinned commits. This repository does not contain the complete upstream trees;
it publishes a recipe, this project's patches, and the disclosed 0010/0012
change in `ci/baseline-changes.patch`. No upstream permission is claimed.
See [`LEGAL.md`](LEGAL.md).
