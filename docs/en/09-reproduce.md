# 09 — Reproduce

**English** · [中文](../zh/09-reproduce.md)

> The success-path scope, bundle hashes and non-guarantees are in
> [`../../GUARANTEE.md`](../../GUARANTEE.md).

The kernel build is reproducible. The boot image and the iOS root are not fully
self-contained here: Apple's userland is not distributable, and the 0085/0084
images used the upstream shim/loader/ADT builder, which is not included as source. This chapter
states what you can reproduce from this repo and what you must supply.

## What you must supply

- An unlocked `ruby` (Redmi Note 12 Pro 5G / MT6877) on Android 12.
- An iPhone X iOS 16.7.16 (20H392) IPSW and an iOS root image.
- A known-good full 128 MiB Magisk/stock boot image for recovery.
- A12 TWRP for `ruby` for offline I/O.
- A GitHub account for the macOS kernel workflow.

## Build the kernel

`.github/workflows/xnu.yml` runs `ci/prepare-baseline.sh`. The recipe takes the
82-file baseline (private mirror; `ALLOW_PUBLIC_UPSTREAM=1` is the external
fallback), verifies the manifest root, adds this project's patches, applies the
small 0010/0012 change, normalizes line endings, and refuses to build unless
the canonical patchset hash matches. See
[`11-ci-baseline.md`](11-ci-baseline.md) for the mirror/secrets boundary.
For the public fallback, run
`ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>`.

```text
apple:    apple-oss-distributions/xnu @ xnu-8796.141.3 (f625db25...)
baseline: 82 files (sweet 0001-0079), manifest root 829d7598...
recipe:   ci/prepare-baseline.sh (no upstream tree copied here)
patchset: 27894e7b... (main, 137 files)
          USB branch: 29449e32... (135 files), config/0131b.env
dxb:      blacktop/darwin-xnu-build @ 663906528d1cd5ea8fde7de6f16de73db9511549
runner:   macos-14, Xcode 15.0.1, macOS 13.5 xnu
config:   DEVELOPMENT, MACHINE_CONFIG=SWEET, -mcpu=cortex-a55
```

Main builds the ramdisk/0140 set and includes the USB series through 0131b.
The 0086/0085 references below are historical.

Run it from **Actions → xnu → Run workflow**, or push a change under `ci/`,
`patches/`, `config/` or the workflow. Artifacts: `xnu-kernel` and
`xnu-buildtree`.

## Rescue root (2026-10-29)

The ramdisk line adds a 4 MB HFS+ root in the LK ramdisk slot. The kernel imports
it with `rubyrdsz=` and mounts it as `md0`; PID 1 runs `/etc/rc` and the
applets in-process, so the minimal root does not depend on launchd or
fork/exec. The rescue image (`6795d9e4...`) and the root are external; the B1
image is `49a10e49...`. The full Unix/iOS environment stays on the UFS iOS
root.

## Host pipeline

The host pipeline uses <1 GiB artifacts and never touches the 16 GiB root. The
shim and ADT are external; the upstream payload tools are fetched at the pinned
baseline commit.

```sh
sh scripts/build-payload.sh --kernel <kernel> --adt <adt> \
  --cmdline-file config/0085-boot.cmdline --out <payload.bin>

python tools/image/pack_boot.py --base <magisk.img> --shim <Image> \
  --payload <payload.bin> --out <boot.img>

python tools/image/boot_layout.py --image <boot.img> \
  --config config/0085.env --payload <payload.bin> --base <magisk.img>
```

`--golden <boot.img>` is optional; the config pins are enough for an external
user without the golden image. The root is prepared separately per
[`root-recipe.md`](root-recipe.md).

The three commands above are the 0085 path. `scripts/test-pipeline.sh` is the
0084 milestone harness and is pinned to `config/0084.env`; it does not test
0085 unless its defaults are updated.

The 0085 real-touch inputs produce payload
`dbc57e96396f2e3e23213a76d300b1a329e2b4a320bc7363cf99ce0fc9e52b1c`.
The booted image is `ace60d1645ec271cdbd55b7007456cb578168ca708382aafae8fbf506e68f6c8`;
the CI-rebuilt kernel was packed to
`54d1b3066a3782cab36135dbe8d666cf53bbd6837b8394105d7e61de9b32b10d` (not
flashed). These images used a random filler, so verify layout, not the image
SHA, for a rebuild.

Previous milestone: the 0084 inputs produce payload
`50701e81...`; the seed `0x84` rebuild is `a0ce0fe1...` and is
layout-equivalent to `94c639d1...`, not byte-identical.

2026-10-22: the B+NOP first boot -> A' and the CI kernel boot were run on the
author's unit. The CI kernel used payload ref `33852e3`, not the pinned
`5095ac1`. A' is a first-boot snapshot; a second-unit/clean-room run is still
open.

## Pack the boot image

The 0084 image used the upstream loader/ADT builder. This repo carries the early
`src/bringup` packers and the offline verifier, but not the upstream loader
source. Use the baseline's `shim/` and `tools/` for a full rebuild, or supply
your own packer.

Rules that must hold:

- Full 128 MiB image; keep DTB, AVB0 and AVB footer at stock offsets.
- Kernel slot exactly 16,606,685 B (FEXTRA padding, no trailing zeros).
- Payload at the expected entry; keep the ARM64 Image header.
- Verify with `tools/image/boot_verify.py` before flashing.

## Flash

Flashing writes the whole 128 MiB image to `boot_a`; it does not change the
root partition. Keep the Magisk/stock image and TWRP image available. Slot b is
not usable.

```sh
adb reboot bootloader
fastboot devices
fastboot flash boot_a <boot.img>
# slot _a is already active; older fastboot builds may reject --set-active
fastboot reboot
```

## Boot args

`config/0085-boot.cmdline` is the real-touch cmdline. Key arguments:

| Argument | Effect |
|---|---|
| `cpus=6` | six A55 cores |
| `ufsroot=iosroot`, `ufslun=2`, `ufsrw=1`, `rootrw=1` | root device |
| `sweetfb_noconsole=1`, `sweetfb_hz=30` | display/debug |
| `sweetgt=1` | enable the Goodix driver; `0` disables it |

The 0084 synthetic-swipe milestone uses `config/0084-boot.cmdline` with
`sweetautoswipe=90000`, `sweetautoswiperetry=15000` and
`sweetautoswipeattempts=3`; `0085` omits those so only real touch drives the UI.

## Expected behavior

- All timings are from the Apple logo. First boot after the patch: ~58 s; warm
  reboot: ~22 s (boot23). The 2026-10-22 B+NOP first boot was observed at 22 s
  to lock screen and 30 s to autoswipe, measured from the Apple logo
  (cache-warm; observation, not fixed timing). Upstream's first boot is
  4–5 min.
- Lock screen: date starts at `Wednesday, December 31` (no RTC/NTP); clock
  advances; camera icon and home bar.
- A real bottom-edge swipe unlocks to the home screen with the 0085 kernel;
  two contacts are dispatched and edge works, but a user-visible pinch was not
  separately instrumented. The 0084 synthetic swipe also unlocks.
- Black wallpaper, `Waiting...` widgets and a Messages badge may remain.
- Real touch works with the 0085 kernel (bottom-edge unlock, two-contact
  dispatch, edge). Keys, Wi-Fi, GPU and RTC are not implemented; USB is a probe
  only (0131b), not a usable interface.
- Pre-boot image hashes are fixed; post-boot live-root/ring/log hashes and
  timing are volatile (see the "Hash stability" section of `GUARANTEE.md`).

## Verify

```sh
python scripts/verify-local.py
python tools/image/boot_verify.py <boot.img> <base.img>
```

`boot_verify.py` prints the image SHA, page/kernel size, SWEETXNU fields, ADT
SHA and cmdline; the optional base comparison checks the tail outside the
kernel slot.

## Recovery

See [`08-recovery.md`](08-recovery.md). Keep a full restore image before every
flash; there is no recovery partition and no `fastboot boot`.
