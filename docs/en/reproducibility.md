# Reproducibility (theoretical)

**English** · [中文](../zh/reproducibility.md)

This repository publishes the success path under **Tier B**: own patches,
tools and documentation; the upstream tree is fetched by a recipe, not copied
into this repository; no full delta and no Apple/Android binaries. The guarantee is
documented and theoretical, not an independently reproduced device guarantee.

**Baseline source (2026-10-29):** CI fetches the 82 files of 0001-0079 from a
private content-addressed mirror. The public pin is the manifest root
`829d7598...` (82 files, LF-normalized), not a repository URL; the repo, ref
and read-only deploy key live in Actions secrets (`BASELINE_REPO`,
`BASELINE_REF`, `BASELINE_SSH_KEY`). External users can use the public
fallback `ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh`, which verifies
the same manifest root.

Main (2026-10-29 integration, squashed from `merge-ramdisk-usb-2026-10-29`) builds the ramdisk set
(`27894e7b...`, 137 files); the `usb-0131b-probe-write` branch builds
`29449e32...` (135 files) and keeps `config/0131b.env`. Both use the same
82-file baseline and the same private-mirror credentials.

## What is published

- `patches/` — 0080 UFS, 0084 autoswipe, historical 0081-0083.
- `ci/prepare-baseline.sh` — take the pinned baseline from the private mirror
  (or the explicit public fallback), verify the manifest root, add this
  project's patches, apply the small 0010/0012 change.
- `ci/baseline_manifest.py` — 82-file baseline manifest root check (LF).
- `ci/patchset_hash.py` — canonical patchset hash (main: 0140, 137 files;
  USB branch: 0131b, 135 files).
- `ci/baseline-changes.patch` — the small 0010/0012 change only.
- `tools/image/`, `tools/twrp/`, `scripts/check-bundle.py` — offline checks.
- `scripts/build-payload.sh`, `tools/image/pack_boot.py`,
  `tools/image/boot_layout.py`, `scripts/test-pipeline.sh` — host pipeline.
- `config/0086.env` — USB P0 build/test cmdline; `config/0085.env` holds the
  0085 artifact hashes and boot cmdline (`0084.env` is the previous milestone).

## What is not published

- `ci/ruby-baseline.diff` or any full upstream delta (removed from history).
- Apple firmware, iOS root, dyld shared caches.
- Stock/Magisk/TWRP boot images.
- Device-baseline hashes (GPT/boot/vbmeta); see `device.md`.
- Full logs, device dumps, diff data, media (deferred).

## Drift controls

| Control | What it prevents |
|---|---|
| Baseline manifest root `829d7598...` + upstream `5095ac1` | baseline content or upstream branch drift |
| Private mirror ref (Actions secret) | mirror tampering; a different root stops the build |
| Fixed topaz deletion list | patch leftovers on the public fallback |
| Fail-closed recipe | missing files or changed 0010/0012 context |
| LF normalization | Windows/macOS line-ending drift |
| `PATCHSET_SHA256` (per branch) | any patchset content change; integration `27894e7b...`, USB `29449e32...` |
| `ci/baseline-changes.patch` SHA | baseline change drift |
| `check-bundle.py` | wrong kernel/boot/root/ICL/cmdline |
| Pinned Actions by SHA | CI supply-chain drift |
| `permissions: contents: read` | over-privileged CI token |
| Xcode 15.0.1 pin | build-tool drift |
| Clean git history | accidental publication of the old delta |

## Host pipeline status

The host stages are present and tested with the 0084 inputs: payload
`50701e81...`, deterministic rebuild `a0ce0fe1...`, layout PASS against the
golden image (and without it, via config pins); only the filler bytes differ.
Linux host CI was green before the final docs/template-only amendment; see
Actions (`verify-local` and the TWRP cross-build on Ubuntu). The shim and ADT remain external;
the 16 GiB root is not touched. A byte-identical rebuild of the original image
is not possible because its filler was random.

## What can still break

- The private mirror or its deploy key becomes unreachable; restore it from
  the local bundle, or use the explicit public fallback.
- The `macos-14` runner image or Xcode 15.0.1 disappears; the workflow fails
  loudly by design.
- Homebrew package versions change; they are recorded but not pinned.
- The root/boot artifacts are lost or replaced.
- The device firmware/GPT/panel differs from `device.md`.
- The ICL offset is version-specific; a different root does not match.
- A byte-identical rebuild of the original boot image; its filler was random.

## Testing status

No device regression tests were run for this packaging. The home-screen result
is historical (boot23); CI builds the kernel only. The exact device effect is
conditional on the same root/boot artifacts and device class. See
[`../../GUARANTEE.md`](../../GUARANTEE.md).
