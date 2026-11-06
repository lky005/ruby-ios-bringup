# Build provenance

`.github/workflows/xnu.yml` builds the ruby kernel without copying the
upstream tree into this repository. The baseline is a content-addressed 82-file set (sweet
0001-0079); this project's patches are the delta.

## Baseline source

The workflow fetches the baseline from a private mirror. The repo, ref and a
read-only deploy key are stored as Actions secrets (`BASELINE_REPO`,
`BASELINE_REF`, `BASELINE_SSH_KEY`); the public pin is the manifest root
`829d7598...` over the 82 LF-normalized files. Nothing in this repository
contains the mirror URL.

External users can run the same recipe against the public upstream:

```sh
ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh /tmp/base
```

That path fetches `MakrSas/ios-topaz` at `5095ac1`, removes the 24 topaz
patches, and verifies the same manifest root.

## Recipe

1. Take the 82 baseline files (`0001-0079`; 79 `.patch` + 3 `.sh`) from
   `BASELINE_DIR` (or the public fallback), normalize to LF, and verify
   `ci/baseline_manifest.py` against the manifest root and file count.
2. Add this project's patches: 0080 UFS, 0084 autoswipe, 0085 Goodix SPI,
   0086-0131b USB, 0140 ramdisk import, 0141 USB decouple, 0142 EP2 MPS 512,
   0143 EP2 frames/rearm, 0144 read-only board probe/REPL, 0145 enumeration
   window, 0146a-0155 probe/pwrap, keys/reboot, battery and touch, 0156-0179
   HAL/I2C, USB hotplug, RubyGIC/KPD and the native EINT touch line, and the
   historical 0081-0083.
3. Apply `ci/baseline-changes.patch`, the small 0010/0012 change for the ruby
   framebuffer addresses.
4. Normalize every `.patch`/`.sh` to LF.
5. Compute the canonical patchset hash over the sorted per-file SHA256 values
   and refuse to build unless it equals `10b1e2e8...` (175 files).
6. Fetch `blacktop/darwin-xnu-build` at `6639065`, copy the patchset, and
   build on `macos-15` with Xcode 16.0.
7. Hash the built Mach-O with `ci/kernel_hash.py`. When
   `KERNEL_EXPECT_EXEC_DATA` is set, the gate compares the exec-data hash
   (`__TEXT_EXEC` plus the data segments, excluding `__TEXT` cstrings and
   `__LINKEDIT`). Full-file hashes may differ between checkouts because of
   DWARF/path metadata; the manifest root, patchset hash and exec-data hash
   are the reproducibility gates.

The full upstream tree and `ci/ruby-baseline.diff` are **not** in the repo.

## Branches

- `main` (2026-11-06 integration, `22cdb29`): patchset `10b1e2e8...` (175 files),
  config `config/0179.env`, workflow `xnu-0179`. It combines the 0156-0174
  HAL/keys/USB/battery work with the 0175-0179 native IRQ and touch line
  (RubyGIC/KPD, EINT parent/child, oneshot WorkLoop, retry/soft reset).
- `main` (2026-11-02 integration, historical): patchset `da13b6df...`
  (151 files), config `config/0155.env`, workflow `xnu-0155`. It combines the
  P1 probe/pwrap (0144/0145/0146a/0147/0148), P2 keys/reboot/battery
  (0149/0150/0152/0152b/0154) and P3 touch re-enable (0155, shared I2C5
  IOLock).
- `main` (2026-11-01 integration): patchset `9f7b41cf...` (141 files), config
  `config/0144.env`. It combines the ramdisk line (0080/0084/0085, 0140/0141),
  the USB series through 0143, the read-only board probe (0144) and the
  enumeration window (0145).
- `usb-0131b-probe-write`: patchset `29449e32...` (135 files), config
  `config/0131b.env`. It keeps its own branch workflow and patch list; the
  same 82-file baseline and mirror credentials apply. The 0131b control
  kernel is recorded in that config.
- `usb-0142-mps512`: patchset `d0c5ab5e...` (138 files), config
  `config/0142.env`. EP2 IN bulk MPS 64 -> 512 (descriptor bytes 4/5 `0, 2`
  and `TX2CSR0` MAXPKTSZ; the 512 B FIFO segment already covers it), frames
  stay 63 bytes, the OUT endpoint stays 64. Built with the 0142 cmdline
  (`rubyusb=1 rubyusb_window_ms=30000 rubyprobe=1`).
- `usb-0143-frame511`: patchset `f47f4c19...` (139 files), config
  `config/0143.env`. Builds on 0142: one log frame per GPD, 16 B header +
  up to 495 B text = 511 bytes (one byte below the 512 B MPS, so each GPD
  ends on a short packet); the reset/rearm path resets the TX ring after
  stopping the QMU. CI `41022192026`; kernel full `d2eae74d...`, exec-data
  `6fa65088...`. The host-side first-session XACT remains open.
- `p0-probe`: patchset `9f7b41cf...` (141 files), config `config/0144.env`.
  Adds `bsd/dev/ruby_probe.c` and the read-only pwrap/I2C/GPIO/clock/KPD/WDT
  command set to the USB console; the test cmdline uses `sweetgt=0` so the
  probe owns I2C5, and 0145 widens the enumeration window. CI `41222632828`;
  kernel full `9c82ea75...`, exec-data `62a17d48...`; image `66352038...`.

The current line is `config/0179.env` / `config/0179-boot.cmdline`.
`config/0155.env` keeps the 2026-11-02 line; `config/0144.env` keeps the
2026-11-01 probe-line reference; `config/0143.env` keeps the previous USB-line
reference; the earlier entries above are historical branches.

## Pins

| Item | Value |
|---|---|
| Baseline manifest | `829d759826607027bc4a1d9818b6dd4956a312a087217b6ce7e5ce31fa3ae910` (82 files) |
| Baseline upstream | `MakrSas/ios-topaz` @ `5095ac19dbdcf37b64b81fe443f4027ad51b84bf` (fallback/provenance) |
| Apple xnu | `xnu-8796.141.3` (`f625db25f47631424dc62ac1c3414b6e530f7e8a`) |
| Patchset (2026-11-06) | `10b1e2e878d331f3a6755eecb3539c05e7df03da5d0a4bf816b7862b1b0541a5` (175 files), `config/0179.env` |
| Patchset (2026-11-02) | `da13b6df7cb9498f4d7b96a69e88be2af9632157829d26514af7ea5f1de8bea0` (151 files), `config/0155.env` |
| Patchset (2026-11-01) | `9f7b41cf26cc495ce1c0fcfacabcd27bf607b13718218c90809d200d53f1e011` (141 files), `config/0144.env` |
| USB line patchset | `f47f4c19c138d0f2e4bf6b0d6ac53dc895bc216c1084c0f4dd41c09b332edb4c` (139 files), `config/0143.env` |
| 0010/0012 change | `ci/baseline-changes.patch`, SHA256 `1edb6633...` |
| XNU harness | `blacktop/darwin-xnu-build` @ `663906528d1cd5ea8fde7de6f16de73db9511549` |
| Runner | `macos-15`, Xcode 16.0, macOS 13.5 xnu |
| Config | `DEVELOPMENT`, `MACHINE_CONFIG=SWEET`, `-mcpu=cortex-a55` |
| 0179 kernel | full `2b008e52...`, exec-data `a4fb021e...`; CI `42114854911`; gate `42115985782`; host-checks `42115991259` |
| 0155 kernel | full `491f2373...`, exec-data `2e98fd85...`; CI `41354317810`; gate `41355922057` |
| 0144 kernel | full `9c82ea75...`, exec-data `62a17d48...` |
| 0140 kernel | full `3acefe47...`, exec-data `721e5daf...` |
| 0131b USB kernel | full `4e945ce6...`, exec-data `06db2bb3...` (control) |

The reference SHAs are provenance; record the actual artifact hash for each
run in the branch's `config/*.env`.

## Secrets

- `BASELINE_REPO` - `owner/repo` of the private mirror
- `BASELINE_REF` - commit SHA in the mirror
- `BASELINE_SSH_KEY` - private half of a read-only deploy key

Never print them in a workflow step; `PROVENANCE.txt` records only the
manifest root and the upstream commit.

## Local check

```sh
BASELINE_DIR=/path/to/mirror sh ci/prepare-baseline.sh /tmp/base
python3 ci/patchset_hash.py /tmp/base/xnu/patches
python3 ci/kernel_hash.py /path/to/kernel.development.sweet
```

On Windows, set `PYTHON=python`. The recipe normalizes line endings, so the
hash is the same on Windows and macOS. The target directory must not exist.

## Scope

The workflow builds the **kernel** only. The shim, ADT and 128 MiB boot image
packing are separate; see `src/bringup/` and `config/0140.env`. Apple firmware,
the iOS root and device-side boot images are not included.

## History and licensing

The public history must not contain `ci/ruby-baseline.diff` or any full
upstream delta. The full baseline is not redistributed; only the manifest root
and the disclosed 0010/0012 change (`ci/baseline-changes.patch`) are published.
The upstream projects had no license file at the pinned commits; obtain
permission or keep the recipe private before public redistribution. See
`../docs/records/LEGAL.md`.
