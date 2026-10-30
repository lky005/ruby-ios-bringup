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
| main (2026-10-30 integration) | `f47f4c19...` | 139 | `config/0143.env` | full `d2eae74d...`, exec `6fa65088...` (CI `41022192026`) |
| main (2026-10-29 integration) | `27894e7b...` | 137 | `config/0140.env` | full `3acefe47...`, exec `721e5daf...` |
| USB 0142 / 0143 branches | `d0c5ab5e...` / `f47f4c19...` | 138 / 139 | `config/0142.env`, `config/0143.env` | CI `41015790742` / `41022192026` |
| USB (`usb-0131b-probe-write`, historical) | `29449e32...` | 135 | `config/0131b.env` | full `4e945ce6...`, exec `06db2bb3...` |

- Main includes 0080/0084/0085, 0086-0131b, 0140/0141, 0142 and 0143.
- 0142 widens the EP2 IN bulk MPS to 512; 0143 grows each log frame to
  511 bytes (16 B header + up to 495 B text) and resets the TX ring on
  rearm after stopping the QMU. The host-side first-session XACT remains
  open in 0143.
- The 0131b branch keeps its own workflow and patch list; main carries
  `config/0131b.env` and `config/0131b-boot.cmdline` as history.
- Kernel run `41022192026` built 0143 and matched exec-data `6fa65088...`;
  `41015790742` did the same for 0142 (`99d98d80...`). The 2026-10-29
  runs `40822689195` / `40824668335` remain the historical main/USB
  references.
- The 2026-10-30 row is the 0143 merge candidate; `main` still points at the
  2026-10-29 row until the squashed commit is merged.
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
