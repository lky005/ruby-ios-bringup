# Config

`0140.env` and `0131b.env` record the 2026-10-29 CI pins. `0140` is the ramdisk
line (patchset `27894e7b...`, 137 files); `0131b` is the USB branch
(`29449e32...`, 135 files) and keeps its exact boot args in
`0131b-boot.cmdline`. The kernel baseline is fetched from a private
content-addressed mirror; the public pin is the manifest root recorded in each
file. `ALLOW_PUBLIC_UPSTREAM=1` is the external fallback.

`0085.env` and `0085-boot.cmdline` record the state that first provided real
Goodix touch on 2026-10-22. `0084.env` and `0084-boot.cmdline` are the previous
milestone (synthetic autoswipe). They are provenance, not universal defaults:

- `cpus=6` selects the six Cortex-A55 cores on this `ruby` unit.
- `ufsroot=iosroot`, `ufslun=2` and `sweethw=0` describe the author's
  partition layout.
- `sweetgt=1` enables the Goodix GT9916R bit-bang SPI driver. `sweetgt=0`
  disables it.
- The 0085 cmdline intentionally omits `sweetautoswipe`, so only real touch
  drives the UI.
- `sweetfb_hz=30` and `sweetfb_noconsole=1` are display/debug choices.

`0086.env` and `0086-boot.cmdline` are the USB P0 build/test state: the
89-file 0086 patchset, `rubyusb=1` in the test cmdline, and no booted kernel
pin yet. `rubyusb=0` (the default when the argument is absent) keeps the probe
inert.

`0087.env` and `0087-boot.cmdline` are the P2 diagnostic build: the 90-file
patchset, a 30 s polling EP0 enumeration window, and `ufslogsecs=1` so the
trace is flushed quickly. It is WIP; no booted reference is pinned.

The kernel SHA and image SHA in `0085.env` are from the build that booted.
A CI rebuild is not promised to be byte-identical; the canonical patchset hash
and the Mach-O exec-data hash are the gates. The boot image itself is not
included.

The workflow runs `ci/prepare-baseline.sh` and gates on the patchset hash; it
does not pack the boot image. See `../ci/README.md` and `../src/bringup/`.

Device-baseline hashes (GPT/boot/vbmeta) are intentionally **not** published;
they can fingerprint the unit. The device situation is described in
`../docs/en/device.md` and `../docs/zh/device.md`. Artifact hashes stay here.

Host pipeline pins: `SHIM_SHA256`, `PAYLOAD_SHA256`, `ADT_SHA256` and
`BASE_BOOT_SHA256` are external inputs; `PAYLOAD_OFF=0x14000`.

The `PAGE`/`KERNEL_SIZE`/`RAW_LEN`/`SHIM_SIZE`/`SWEETXNU_*` values are the
expected layout for `boot_layout.py --config`; they remove the golden-image
dependency.
