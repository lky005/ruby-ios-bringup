# 11 — CI baseline and branch pins

**English** · [中文](../zh/11-ci-baseline.md)

> Status tags follow the [repository README](../../README.md): **[measured]**,
> **[inferred]**, **[historical]**. A number without a source is a bug.

The kernel CI no longer depends on a live upstream repository. It assembles the
kernel from Apple's xnu tag, a content-pinned 82-file baseline, and this
project's delta.

## Baseline [measured]

- 82 files: 79 `.patch` plus 3 staging `.sh` (sweet 0001-0079).
- Manifest root `829d7598...` over the LF-normalized files; `MANIFEST.sha256`
  lists each file. The public pin is the root, not a repository URL.
- CI fetches the set from a private content-addressed mirror. The repository,
  ref and a read-only deploy key are Actions secrets (`BASELINE_REPO`,
  `BASELINE_REF`, `BASELINE_SSH_KEY`). No mirror URL or key is published.
- Apple source: `apple-oss-distributions/xnu` tag `xnu-8796.141.3`
  (`f625db25...`), cloned by the build harness.

## Branches and pins [measured]

| Line | Patchset | Files | Config | Kernel reference |
|---|---|---|---|---|
| main (2026-10-29 integration) | `27894e7b...` | 137 | `config/0140.env` | full `3acefe47...`, exec `721e5daf...` |
| USB (`usb-0131b-probe-write`) | `29449e32...` | 135 | `config/0131b.env` | full `4e945ce6...`, exec `06db2bb3...` |

- Main includes 0080/0084/0085, 0086-0131b, 0140 and 0141.
- The USB branch keeps its own workflow and patch list. Main carries
  `config/0131b.env` and `config/0131b-boot.cmdline` as its reference.
- Kernel run `40822689195` was executed on the ramdisk line before the merge
  and matched exec-data `721e5daf...`; `40824668335` did the same for the USB
  line. The pre-merge branch was checked by host-checks `40828162023`; the
  main squash uses the same patchset gate.
- Main is the combined line (squashed from
  `merge-ramdisk-usb-2026-10-29`); the pins are `config/0140.env` and
  `config/0131b.env`.
- A rebuilt kernel's full SHA differs from the reference in `__TEXT` metadata
  and the compressed `__CTF` segment. Every code/data segment and `__LINKEDIT`
  is identical; the exec-data hash is the gate.

## Recipe

1. Fetch the 82-file baseline (private mirror, or the public fallback
   `ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>`), normalize to LF
   and verify the manifest root.
2. Add the branch's project patches, apply the 0010/0012 change, normalize and
   verify the canonical patchset hash.
3. Build with `blacktop/darwin-xnu-build` on `macos-14` with Xcode 15.0.1.
4. Gate the kernel's exec-data hash.

## Local check

```sh
BASELINE_DIR=<baseline> sh ci/prepare-baseline.sh <dest>
# public fallback
ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>
python ci/baseline_manifest.py --patches <dest>/xnu/patches \
  --expect-root <manifest-root> --expect-count 82
python ci/patchset_hash.py <dest>/xnu/patches
python scripts/verify-local.py --ci-config config/0140.env
```

The USB branch passes `--ci-config config/0131b.env`.

## Boundaries

- The private mirror URL, deploy key and baseline code are not published.
- Apple firmware, the iOS root, shared caches and boot images are not
  published.
- The upstream projects had no license file at the pinned commits; keep the
  mirror private. The full baseline is not redistributed; only the manifest
  root and the disclosed 0010/0012 change in `ci/baseline-changes.patch` are
  published.
- External users can use the public upstream fallback; the manifest root
  verifies the same content.
