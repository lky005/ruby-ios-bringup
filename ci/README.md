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
   0086-0131b USB, 0140 ramdisk import, 0141 USB decouple, and the
   historical 0081-0083.
3. Apply `ci/baseline-changes.patch`, the small 0010/0012 change for the ruby
   framebuffer addresses.
4. Normalize every `.patch`/`.sh` to LF.
5. Compute the canonical patchset hash over the sorted per-file SHA256 values
   and refuse to build unless it equals `27894e7b...` (137 files).
6. Fetch `blacktop/darwin-xnu-build` at `6639065`, copy the patchset, and
   build on `macos-14` with Xcode 15.0.1.
7. Hash the built Mach-O with `ci/kernel_hash.py`. When
   `KERNEL_EXPECT_EXEC_DATA` is set, the gate compares the exec-data hash
   (`__TEXT_EXEC` plus the data segments, excluding `__TEXT` cstrings and
   `__LINKEDIT`). Full-file hashes may differ between checkouts because of
   DWARF/path metadata; the manifest root, patchset hash and exec-data hash
   are the reproducibility gates.

The full upstream tree and `ci/ruby-baseline.diff` are **not** in the repo.

## Branches

- `main` (2026-10-29 integration, squashed from
  `merge-ramdisk-usb-2026-10-29`): patchset `27894e7b...` (137 files), config
  `config/0140.env`. It combines the ramdisk line (0080/0084/0085, 0140/0141)
  with the USB series through 0131b.
- `usb-0131b-probe-write`: patchset `29449e32...` (135 files), config
  `config/0131b.env`. It keeps its own branch workflow and patch list; the
  same 82-file baseline and mirror credentials apply. The 0131b control
  kernel is recorded in that config.

Main keeps `config/0131b.env` and `config/0131b-boot.cmdline` as the USB
branch reference. The kernel built on it is the ramdisk set, which contains
every USB patch through 0131b plus 0140/0141.

## Pins

| Item | Value |
|---|---|
| Baseline manifest | `829d759826607027bc4a1d9818b6dd4956a312a087217b6ce7e5ce31fa3ae910` (82 files) |
| Baseline upstream | `MakrSas/ios-topaz` @ `5095ac19dbdcf37b64b81fe443f4027ad51b84bf` (fallback/provenance) |
| Apple xnu | `xnu-8796.141.3` (`f625db25f47631424dc62ac1c3414b6e530f7e8a`) |
| Patchset | `27894e7b274ea57131b5ee57799eb13c1ca2ddd7a6d9e38c15468cdd0dd55ce9` (137 files) |
| USB branch patchset | `29449e32a638e8e44e1683fc711b4f0dbba89c273310e74baf802653caf1eda3` (135 files), `config/0131b.env` |
| 0010/0012 change | `ci/baseline-changes.patch`, SHA256 `1edb6633...` |
| XNU harness | `blacktop/darwin-xnu-build` @ `663906528d1cd5ea8fde7de6f16de73db9511549` |
| Runner | `macos-14`, Xcode 15.0.1, macOS 13.5 xnu |
| Config | `DEVELOPMENT`, `MACHINE_CONFIG=SWEET`, `-mcpu=cortex-a55` |
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
`LEGAL.md`.
