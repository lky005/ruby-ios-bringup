# Verification

This file records what was actually checked, and what was not. It is updated
after each verification pass.

## Environment

- Host: Windows 10 (build 26300), Git Bash, Python 3.13.13.
- 2026-10-21: no phone attached; source artifacts were read-only inputs.
- 2026-10-22: device runs with TWRP 3.7.0_12-0; the iOS side has no USB. Root
  scans were read-only; `boot_a` was written for TWRP/reference/CI images; the
  root was restored to A/B+NOP only after a live-backup scan.

## Host-verified (2026-10-21, updated 2026-10-22)

`python scripts/verify-local.py` with the optional external inputs:

| Check | Result |
|---|---|
| Python syntax | 18 files, pass |
| Shell syntax | 7 files, pass |
| Forbidden binary/media files | none outside the allowlist |
| Sanitized media | 2 allowlisted files; SHA-256 in `media/README.md` |
| Personal paths / secrets | none |
| Synthetic ICL round-trip | pass (dry-run, apply, wrong-bytes negative case) |
| Real ICL 4K block round-trip | pass: `ae3178046fe7cb9e08291c39dc4773429be26c35472c6fbd9135d5f2a225fd73` -> `4a4895422dcec766b90b65c067ecb06ef8fd3e346c03ee7e2464a85f62a73b74` |
| Patch 0081 apply-check | pass on a local pre-0084 tree |
| Patch 0083 apply-check | pass on the same tree |
| Patch 0084 apply-check | pass on the same tree |
| Patch 0080 reverse-check | pass (already applied in that tree) |
| Patch 0082 reverse-check | pass (already applied in that tree) |
| Boot image layout dump | pass on the external 0084 image |
| Host pipeline (payload/pack/layout) | pass: payload `50701e81...`; pack seed `0x84` -> `a0ce0fe1...`; layout PASS vs 0084; only filler bytes differ |
| Strict host bundle | pass: kernel/boot/shim/payload/base/cmdline (root/ICL optional) |
| Config-mode layout | pass without golden; 11 pinned checks |
| Linux host CI | pass before the final docs/template-only amendment; see Actions |

## CI-verified (2026-10-29)

| Check | Result |
|---|---|
| Baseline manifest | 82 files, root `829d7598...`, manifest matches |
| Patchset (main, 2026-10-29) | `27894e7b...` (137 files) |
| Patchset (USB branch) | `29449e32...` (135 files) |
| Kernel exec-data (main line) | `721e5daf...` (matches the booted 0140/B1 reference) |
| Kernel exec-data (USB) | `06db2bb3...` (matches the 0131b control) |
| Full-file A/B | differs only in `__TEXT` metadata and `__CTF`; all code/data segments and `__LINKEDIT` identical |
| Pre-merge CI | `40822689195` (ramdisk line), `40824668335` (USB line) success; pre-merge host-checks `40828162023`; main squash uses the same patchset gate |
| Host checks | `scripts/verify-local.py --ci-config config/0140.env` and `config/0131b.env` pass |
| Sanitization | private mirror URL/key absent from public docs; build logs scanned, 0 hits |
| Device | no flash for this change |

The baseline is fetched from a private content-addressed mirror; the public pin
is the manifest root. See `docs/en/11-ci-baseline.md`.

Boot image fields reported by `tools/image/boot_verify.py`:

- image SHA256: `94c639d1f45197718c62bd09c32c72b39710ba23de60f4a04bba96014bce1cb6`
- page / kernel size: 2048 / 16,606,685
- decompressed payload: 37,449,728 bytes
- SWEETXNU: version 1, 10 segments
- ADT SHA256: `c778d4b5a559ad7c4e8f54113cc8b4e7d91d34082efc91acb02e1fcce0099720`
- cmdline includes `cpus=6`, `ufsroot=iosroot`, `ufslun=2`, `sweetfb_hz=30`,
  `sweetautoswipe=90000`, `sweetautoswipeattempts=3`

The ICL blocks, boot image and XNU tree are **not** in this repository. The
hashes above are recorded as evidence; the inputs stay outside the repository.

## Build recipe (0085)

The workflow `.github/workflows/xnu.yml` fetches `MakrSas/ios-topaz` at
`5095ac1`, runs `ci/prepare-baseline.sh`, and refuses to build unless the
canonical patchset hash is
`cf4008e309cfa566e3df968592a2d3f3224a9b3d0813d6054326115fecc0a03f`
(88 files). The recipe removes the topaz patches, adds this project's patches
(0080, 0084, 0085, historical 0081-0083), applies the small 0010/0012 change,
and normalizes line endings.

The same 88-file canonical patchset built the booted 0085 kernel in the
harness; the patchset hash is the source-identity gate. After the build,
`ci/kernel_hash.py` hashes the Mach-O segments. Full-file hashes may differ
between checkouts because of DWARF/path metadata; the workflow gates the
**exec-data** hash (`__TEXT_EXEC` plus data segments, excluding `__TEXT`
cstrings and `__LINKEDIT`) against `e4823afb...`.

Locally (Windows):

- the recipe was run against a fresh `topaz@5095ac1` checkout in a temp dir;
- after the recipe, `patchset_hash.py` reported `cf4008e3...` with 88 files;
  the harness patchset reports the identical hash;
- `ci/baseline-changes.patch` has SHA256 `1edb6633...`;
- `config/0085.env` pins match the workflow and the patchset hash.

The full upstream tree and `ci/ruby-baseline.diff` are **not** in the clean
history. Previous milestone: the 0084 patchset `de1824c2...` (87 files), kernel
`b38fca5f...`/`8a80855d...`, image `94c639d1...`.

### CI rebuild (0085)

- Run `39694456200` on branch `touch-0085`, head `042ec31`, workflow_dispatch;
  conclusion **success**.
- Patchset gate: `cf4008e3...` (88 files), identical to the harness build.
- CI kernel: full `904e10df...`, size 17,226,832; exec-data `e4823afb...`,
  **identical to the booted kernel**.
- Per-segment: `__TEXT_EXEC` `e9f67a2a...` and `__DATA_CONST` `38f78ce4...`
  match the booted kernel; `__TEXT` and `__LINKEDIT` differ because of build
  paths/DWARF, so the full SHA differs. This is the documented distinction.
- The CI kernel was packed locally to image `54d1b306...`; layout is identical
  (kernel slot 16,606,685, raw 37,449,728, ADT `c778d4b5...`, same cmdline).
  It was **not flashed**.
- Main CI run `39696625623` (head `53dc3a9`) also succeeded: full
  `00cb6cc8...`, exec-data `e4823afb...` (matches), and the same
  `__TEXT_EXEC`/`__DATA_CONST` hashes. The kernel was packed to
  `61f9d24e...`, flashed to `boot_a`, and booted on the author's unit; real
  touch works (one-unit observation).

## Root state audit (2026-10-22)

Read-only audit of the external frozen root image; no device writes.

| Check | Result |
|---|---|
| A success snapshot SHA-256 | `e698339d...` |
| B pre-boot22 SHA-256 | `985c30...` |
| C clean base SHA-256 | `34c2882d...` |
| A' first-boot snapshot SHA-256 | `55e2ab2c...` (one first boot; not stable across runs) |
| boot22 block set | 62,490 4K blocks; all match post-boot22 |
| whole-image CRC scan vs pre-boot22 baseline | exactly 62,490 changed; 0 extra, 0 missing |
| pre-boot22 reconstruction | replacing those blocks with the recorded original blocks yields `985c30...` |
| ICL block 2438140 | `4a489542...` (NOP) |
| structural spot-check | launchd, dyld, systembag, containers, ByHost, LastSystemVersion=20H392 |

The local frozen root is A. The previous `ROOT_SHA256=985c30...` named B
(pre-boot22); it was corrected to A on 2026-10-22. A' is the first-boot
snapshot from B+NOP; a new first boot is a new state. Hashes only; no personal
paths or device identifiers.

## Guarantee status (2026-10-22)

- **G1 — host/build:** verified. A fresh clone passes `verify-local.py`; the
  0085 workflow uses the recipe, enforces the canonical patchset hash, and the
  exec-data hash gate. CI run `39694456200` succeeded and matched the booted
  kernel's exec-data hash.
- **G2 — success path:** documented recipe with **one-unit device evidence**
  (B+NOP first boot -> A', and the CI kernel boot). It has not been independently
  reproduced on a second unit or in a clean-room. Pre-boot hashes are the
  contract; post-boot live-root/ring/log hashes are volatile.
- **G3 — author's device:** 2026-10-22: B+NOP first boot at 22 s to lock screen
  (from the Apple logo) and 30 s to autoswipe (observed); 3 autoswipe attempts;
  driverkitd only; A' `55e2ab2c...`. CI kernel `8a80855d...` booted to the home
  screen (driverkitd + PosterBoard; no lsd/SpringBoard/backboardd). The 0085
  kernel `9eb9acac...` then booted with real Goodix touch; a real bottom-edge
  swipe unlocked the screen; 206 down/206 up records, two-contact HID dispatch
  and edge (user-visible pinch not separately instrumented).
- **Deferred:** second-unit boot, Linux clean-room CI, strict pinned payload
  rebuild (the test used ref `33852e3`), root/shim/ADT builders as clean-room
  tools, original ICL block regression, keys/USB, long-run stability.
- Device-baseline hashes are intentionally not published.

The scope, hashes and non-guarantees are in [`GUARANTEE.md`](GUARANTEE.md).

## Hash stability (2026-10-22)

Fixed / pre-boot (identity):

- 0085 patchset `cf4008e3...` (88 files); kernel `9eb9acac...`; exec-data
  `e4823afb...`; boot image `ace60d16...`; payload `dbc57e96...`;
- 0084 patchset `de1824c2...`; reference image `94c639d1...`; CI image
  `87dd4910...`; CI kernel `8a80855d...`; payload `2749bf1c...`;
- named root snapshots: A `e698339d...`, B `985c30...`, C `34c2882d...`,
  A' `55e2ab2c...`.
- A' is one first-boot snapshot; a new first boot is a new state. Kernel CI
  builds are not bit-identical; the patchset hash is the gate; record the
  actual artifact hash for the run.

Volatile / post-boot (do not require these to match):

- the live root after any boot (A' -> A''), UUIDs/timestamps, logs and caches;
- the SWEETLOG ring and its decoded text;
- UI pixels, timing and crash timing/counts.

The contract is pre-boot identity + behavior (lock screen, autoswipe, desktop,
ring markers), not a post-boot whole-disk hash.

## Device-verified (2026-10-22)

Author's unit; one run. Root images are external.

- Root restore: live vs A scan found 30,606 blocks; the live blocks were backed
  up, A was written, and a re-scan returned 0 changed.
- B+NOP: 62,489 blocks (62,490 boot22 blocks minus the ICL block, which is the
  same NOP in A and B+NOP); re-scan 0 changed; ICL `4a489542...`.
- First boot: observed 22 s to lock screen and 30 s to autoswipe, measured from
  the Apple logo; ring `5a131ad9...` (3 autoswipe attempts, all edge;
  driverkitd only); A' `55e2ab2c...`; A' vs A 67,765 blocks; ICL unchanged.
- CI kernel: run `39648068844`, kernel `8a80855d...`, payload `2749bf1c...`,
  image `87dd4910...`; lock screen -> desktop; ring `480e5e7b...` (3 autoswipe
  attempts; driverkitd + PosterBoard; no lsd/SpringBoard/backboardd); reference
  0084 restored afterwards.
- Caveat: the payload tool came from upstream ref `33852e3`, not the pinned
  `5095ac1`; the strict pinned rebuild is open.

### Real-touch 0085 (2026-10-22)

- Kernel `9eb9acac...` (exec-data `e4823afb...`), image `ace60d16...`; built
  from the 88-file patchset `cf4008e3...` (identical canonical hash to the
  harness build).
- Boot log: `SWEET GT: LDO3 en=80 vout=b0, LDO2 en=80 vout=40`;
  `SWEET GT: rails on en3=c4 en2=c4`;
  `SWEET GT: BERLIN/9916R ready, 1080x2400`.
- `SWEET HID: touch` 413 records: 206 down / 206 up, 40 finger-1 records,
  84 edge records; down x 0–1038, y 5–2399; no stopped/panic/fail.
  `SweetHIDTouch::touch()` appends both active fingers to one digitizer
  collection when both are down; a user-visible pinch was not separately
  instrumented.
- Real bottom-edge swipe unlocked the lock screen; coordinates were not
  inverted. The full SWEETLOG is external and not committed; only the
  sanitized excerpt and aggregate counts are recorded.
- The main-CI rebuild image `61f9d24e...` (kernel `00cb6cc8...`, same
  exec-data) was flashed to `boot_a` and booted on the author's unit; real
  touch works. This extends the one-unit real-touch evidence to the
  main-CI artifact.

## Device-verified (historical)

These results were observed on the author's device during the bring-up. They
are not reproduced by CI and are not a guarantee for another unit or firmware.

- boot22 (first boot after the patch): 58 s; boot23 (warm reboot): 22 s;
  timings from the Apple logo; synthetic autoswipe unlocked to the home screen;
  animations normal.
- ICL NOP: iosroot 4K block 2438140, original `ae317804...`, patched
  `4a489542...`; original block backed up.
- boot22 diff: 62,490 changed 4K blocks (244 MiB); the diff data is not in this
  repository.
- UFS root on LUN 2 and read/write HFS+ were exercised on the device.

## Not verified

- Hardware buttons, USB, Wi-Fi, GPU and RTC.
- Regression of the original (unpatched) ICL block after the first-boot state
  was created.
- A from-scratch reproduction on a different `ruby` unit, a second-unit boot,
  or a clean-room.
- The strict pinned payload rebuild (the CI test used ref `33852e3`).
- The root builder and shim/ADT builder as clean-room tools.

## Media (2026-10-21)

- `media/autoswipe.mp4` and `media/home-screen.jpg` are committed with explicit
  allowlist entries in `scripts/verify-local.py` and `.gitignore`.
- Both were re-encoded; `ffprobe` reports no location, creation time or encoder
  tags, and the clip has no audio stream.
- The 120 s source recording carried GPS metadata and is not in this repository.

## Commands

```sh
python scripts/verify-local.py
```

With external inputs (paths are yours; they are not committed):

```sh
python scripts/verify-local.py \
    --icl-orig <original-4k-block> \
    --icl-patched <patched-4k-block> \
    --xnu-tree <patched-xnu-tree> \
    --boot-image <boot.img>
```
