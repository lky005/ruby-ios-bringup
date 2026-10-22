# Build provenance (0087 WIP)

`.github/workflows/xnu.yml` builds the 0087 ruby USB P2a WIP kernel **without
vendoring the upstream tree**. 0087 extends 0086 with
`patches/0087-ruby-usb-p2a.patch`: a 30 s EP0 trace window that captures
setup attempts and ACK+STALLs them. 0086 is the P0 power/PHY soft-connect
driver; the USB probe is inert unless the boot arguments contain `rubyusb=1`.

## Recipe

1. Fetch `MakrSas/ios-topaz` at the pinned commit `5095ac1`.
2. Remove the 24 topaz-specific patches by name
   (`ci/topaz-patches-to-remove.txt`).
3. Add this project's patches: 0080 UFS, 0084 autoswipe, 0085 Goodix SPI
   touch, 0086 USB P0, 0087 USB P2a, and historical 0081-0083.
4. Apply `ci/baseline-changes.patch`, the small 0010/0012 change needed for
   the ruby framebuffer addresses.
5. Normalize every `.patch`/`.sh` to LF.
6. Compute the canonical patchset hash over the sorted per-file SHA256 values
   and refuse to build unless it equals
   `5142a95dbf41a411c4a20bb400e6c05fa14ad7aabb8636968b861123b2e0cfd3`
   (90 files).
7. Fetch `blacktop/darwin-xnu-build` at `6639065`, copy the patchset, and
   build on `macos-14` with Xcode 15.0.1.
8. Hash the built Mach-O with `ci/kernel_hash.py`. When
   `KERNEL_EXPECT_EXEC_DATA` is set, the gate compares the **exec-data** hash
   (`__TEXT_EXEC` plus the data segments, excluding `__TEXT` cstrings and
   `__LINKEDIT`). `config/0087.env` leaves it empty: this is a WIP trace build,
   so the run records the hashes without gating. Full-file hashes may differ
   between checkouts because of DWARF/path metadata; the patchset hash and,
   once known, the exec-data hash are the reproducibility gates.

The full upstream tree and `ci/ruby-baseline.diff` are **not** in the repo.

## Pins

| Item | Value |
|---|---|
| Baseline | `MakrSas/ios-topaz` @ `5095ac19dbdcf37b64b81fe443f4027ad51b84bf` |
| Patchset | `5142a95dbf41a411c4a20bb400e6c05fa14ad7aabb8636968b861123b2e0cfd3` (90 files) |
| 0010/0012 change | `ci/baseline-changes.patch`, SHA256 `1edb6633...` |
| XNU harness | `blacktop/darwin-xnu-build` @ `663906528d1cd5ea8fde7de6f16de73db9511549` |
| Runner | `macos-14`, Xcode 15.0.1, macOS 13.5 xnu |
| Config | `DEVELOPMENT`, `MACHINE_CONFIG=SWEET`, `-mcpu=cortex-a55` |
| 0085 booted kernel | `9eb9acac...`; exec-data `e4823afb...` (historical reference) |
| 0085 booted boot image | `ace60d16...` |
| 0086 P0 kernel | build only; device result kept private |
| 0087 P2a kernel | pending WIP test |

The reference SHAs are provenance, not a byte-for-byte guarantee for a future
run. Record the actual artifact hash for each run in `config/0087.env`.

## Local check

```sh
sh ci/prepare-baseline.sh /tmp/base
python3 ci/patchset_hash.py /tmp/base/xnu/patches
python3 ci/kernel_hash.py /path/to/kernel.development.sweet
```

On Windows, set `PYTHON=python`. The recipe normalizes line endings, so the
hash is the same on Windows and macOS. The target directory must not exist.

## Scope

The workflow builds the **kernel** only. The shim, ADT and 128 MiB boot image
packing are separate; see `src/bringup/` and `config/0087.env`. Apple firmware,
the iOS root and device-side boot images are not included.

## History and licensing

The public history must not contain `ci/ruby-baseline.diff` or any full
upstream delta. `baseline-changes.patch` contains only this project's small
0010/0012 change; the upstream tree is fetched, not redistributed. The upstream
projects had no license file at the pinned commits; obtain permission or keep
the recipe private before public redistribution. See `LEGAL.md`.
