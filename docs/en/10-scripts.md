# 10 — Scripts

**English** · [中文](../zh/10-scripts.md)

Every tracked script is listed with its purpose, boundary and failure mode.
"Why it exists" matters more than "how to run it": most of these tools exist
because a simpler path silently failed.

## Inventory

| Script | Purpose | Risk | Verified |
|---|---|---|---|
| `tools/image/icl_nop.py` | 4-byte patch in a raw block/image | offline write, dry-run default | real block round-trip |
| `tools/image/dyld_scan.py` | locate a VA in the split dyld cache | read-only | used in the MG work |
| `tools/image/boot_verify.py` | inspect a packed boot image | read-only | 0084/0085 images |
| `tools/twrp/blkdiff.c` | compare an image with a 4K CRC map | read-only on image | multiple boot cycles |
| `tools/twrp/blkpatch.c` | write diff blocks by index | **raw device write** | multiple boot cycles |
| `tools/twrp/twrp-guard.sh` | refuse to run outside TWRP | gate | host refuses |
| `tools/twrp/build.sh` | cross-compile the two static tools | host build | build recipe |
| `src/bringup/build_full_a.py` | pack payload into a boot image slot | offline write | red-screen/probe images |
| `src/bringup/build_shim_full.py` | same for the stage shim | offline write | probe images |
| `src/bringup/mkboot_v2.py` | build a small Android boot image | offline write | early bring-up |
| `src/bringup/repack_stock.py` | repack a stock image with a payload | offline write | early bring-up |
| `src/ufs-probe/build_ufs_full.py` | pack the UFS probe | offline write | UFS probe image |
| `scripts/fetch-base.sh` | clone a pinned baseline for inspection | read-only/network | optional |
| `scripts/verify-local.py` | host-only checks | read-only | passes locally |
| `scripts/check-bundle.py` | verify artifact hashes before flash | read-only | config-driven |
| `.github/workflows/xnu.yml` | build the current kernel | CI build | recipe + patchset hash |
| `ci/prepare-baseline.sh` | fetch baseline, verify manifest, add patches, verify hash | network + temp write | tested locally |
| `ci/patchset_hash.py` | canonical patchset hash (integration: 137 files; USB: 135) | read-only | matches recipe |
| `ci/baseline-changes.patch` | small 0010/0012 change | data | hash pinned |
| `scripts/build-payload.sh` | payload from kernel+ADT+cmdline | network + offline write | tested |
| `tools/image/pack_boot.py` | deterministic 128 MiB boot image | offline write | tested |
| `tools/image/boot_layout.py` | compare rebuilt vs golden layout | read-only | tested |
| `scripts/test-pipeline.sh` | payload → pack → layout (0084 milestone) | temp writes | passes for 0084; 0085 uses the commands in `09-reproduce` |
| `config/0140.env`, `config/0131b.env` | current branch pins and boot cmdlines; 0086 files are historical | data | run/pin checked |
| `config/0085.env`, `0085-boot.cmdline` | provenance (real touch) | data | run/pin checked |
| `config/0084.env`, `0084-boot.cmdline` | previous milestone (synthetic swipe) | data | historical |

## `tools/image/icl_nop.py`

**Why:** The kernel notification was already delivered; the stuck consumer was
a userland MG call. The smallest reversible bypass is a 4-byte `nop`. Patching a
16 GB image in place needed SHA checks and a backup.

- **Inputs:** a 4K block or a raw image + block index.
- **Output:** patched block/image; backup in image mode.
- **Does not:** find the offset, prove the semantic effect, or flash anything.
- **Risk:** offline write; default dry-run.
- **Failure modes:** wrong block/offset → original bytes mismatch; stale backup
  → refuses without `--force`; mounted image → do not use.
- **Example:**

```sh
python tools/image/icl_nop.py --image <root.img> --block-index 2438140 \
  --in-block-offset 0xF0C --expect-block-sha <orig> \
  --expect-patched-sha <patched> --apply
```

## `tools/twrp/blkdiff.c` / `blkpatch.c`

**Why:** A 16 GiB `adb pull` stalled even in chunks. `blkdiff` computes CRC32
on the phone and writes only changed 4K blocks; `blkpatch` writes those blocks
back. A 16 GiB scan takes about 45 s on UFS.

- **Inputs:** image/partition, CRC map, diff/idx, block count.
- **Does not:** create a backup, check mounts, or detect TWRP by itself.
- **Risk:** `blkpatch` writes raw blocks; run through `twrp-guard.sh`.
- **Failure modes:** short read, wrong count, wrong device, mounted filesystem,
  missing `sync`.
- **Example:**

```sh
sh tools/twrp/twrp-guard.sh ./blkdiff /dev/block/by-name/iosroot \
  crc.bin diff.bin diff.idx 16384
```

## `tools/image/dyld_scan.py`

**Why:** `InstalledContentLibrary` lives in one of 26 split-cache files;
guessing offsets wastes boots. This tool parses the main cache and subcaches and
prints the containing image, file offset and first 0x80 bytes.

- **Risk:** read-only.
- **Does not:** extract, patch or modify.
- **Example:**

```sh
python tools/image/dyld_scan.py --cache-dir <dyld-dir> \
  --image-name InstalledContentLibrary --va 0x1b11b9f0c
```

## `tools/image/boot_verify.py`

**Why:** The 128 MiB layout is easy to get subtly wrong (kernel slot, DTB, AVB
footer). Verify the packed payload fields before flashing.

- **Risk:** read-only.
- **Checks:** image SHA, page/kernel size, SWEETXNU header, ADT SHA, cmdline,
  optional tail comparison.
- **Does not:** validate signatures/AVB or flash.

## `src/bringup/build_full_a.py` / `build_shim_full.py`

**Why:** LK expects the stock kernel stream size. The packers preserve the slot
size with a gzip FEXTRA pad, so DTB/ramdisk/AVB stay in place.

- **Inputs:** base image, payload, output.
- **Does not:** sign AVB, flash, or check the device.
- **Failure modes:** payload too large to fit the slot; wrong payload offset;
  non-ARM64 payload.
- **Example:**

```sh
python src/bringup/build_full_a.py --base <stock.img> \
  --payload <payload.bin> --out <out.img>
```

## `src/ufs-probe/build_ufs_full.py`

**Why:** Pack the read-only UFS probe into the same size-preserving slot. The
filler is deterministic (seeded PRNG) so repeated builds match.

- **Does not:** write UFS or flash.
- **Example:**

```sh
python src/ufs-probe/build_ufs_full.py --base <stock.img> \
  --shim <Image> --out <probe.img>
```

## `ci/prepare-baseline.sh` + `.github/workflows/xnu.yml`

**Why:** Upstream has no license file, so the tree is not copied into this
repository and no full delta is published. The recipe takes the content-pinned
82-file baseline (private mirror, or the `ALLOW_PUBLIC_UPSTREAM=1` fallback),
verifies the manifest root, adds this project's patches, applies the small
0010/0012 change, normalizes LF, and verifies the canonical patchset hash
(main: 137 files; USB branch: 135) before building.

- **Does not:** flash, pack an image, follow a moving branch tip, or publish
  the full upstream delta.
- **Failure modes:** baseline manifest mismatch → stop; 0010/0012 context
  mismatch → `git apply` fails; patchset mismatch → stop before the build.
- **Pins:** `config/0140.env`, `config/0131b.env` and `ci/README.md`.
- **Pins:** see `config/0140.env`, `config/0131b.env` and `ci/README.md`.

## `scripts/build-payload.sh`

**Why:** The 0084 payload is deterministic; the 0085 image used a random filler,
so verify its layout. The payload tool lives upstream
and the ADT is external. The wrapper fetches the pinned upstream tools, runs
`mkpayload.py` with the user's kernel/ADT/cmdline, and checks the payload SHA.
The shim and ADT are not in the repo.

- **Inputs:** kernel, ADT, cmdline file, output.
- **Does not:** fetch a kernel/ADT, pack a boot image, or flash.
- **Failure modes:** missing input; baseline mismatch; payload SHA mismatch.
- **Verified:** 0084 inputs produce `50701e81...`.

## `tools/image/pack_boot.py`

**Why:** The original packer used `os.urandom`, so the image SHA was not stable.
This packer uses a seeded SHA-256 filler, preserves the kernel slot size
(FEXTRA), and verifies the shim/payload ranges and the tail.

- **Inputs:** base image, shim, payload, output.
- **Does not:** build the payload, flash, or change the base tail.
- **Failure modes:** shim/payload too large; gzip cannot fit; readback mismatch.
- **Verified:** two runs with seed `0x84` produce the same image
  `a0ce0fe1...`; layout equals the golden 0084 image.
- **Note:** the original `94c639d1...` cannot be byte-reproduced because its
  filler was random.

## `tools/image/boot_layout.py`

**Why:** A rebuilt image has a different SHA by design. This compares the
layout that matters: SWEETXNU fields, ADT, cmdline, shim range, payload range
and the tail.

- **Risk:** read-only.
- **Does not:** flash, modify, or require the root image.
- **Verified:** rebuilt vs golden 0084: all checks PASS; only the image bytes
  differ.
- **No golden:** pass `--config config/0085.env`; the pinned header/ADT/
  cmdline/shim/payload values are compared instead.

## `scripts/test-pipeline.sh`

**Why:** One host-only command to run payload → pack → layout with the external
inputs. It uses <1 GiB artifacts and never touches the 16 GiB root.

- **Does not:** touch a device, flash, or modify the inputs.
- **Example:** see `scripts/README.md`.

## `scripts/check-bundle.py`

**Why:** Before flashing, compare the kernel, boot image, root image, ICL blocks
and cmdline against the success bundle. A mismatch means a different
configuration, not a covered reproduction.

- **Risk:** read-only.
- **Does not:** touch a device or modify an image.
- **Example:**

```sh
python scripts/check-bundle.py --kernel <kernel> --boot <boot.img> \
  --root <root.img> --icl-orig <orig.bin> --icl-patched <patched.bin> \
  --cmdline <cmdline.txt>
```

## `scripts/verify-local.py` + `tools/twrp/twrp-guard.sh`

**Why:** Catch syntax, PII, patchset drift and ICL round-trip errors on the
host; refuse raw-block tools outside TWRP.

- **Risk:** read-only; the ICL test writes only to a temp dir.
- **Does not:** touch a device, flash or modify an image.
- **Example:**

```sh
python scripts/verify-local.py
sh tools/twrp/twrp-guard.sh ./blkdiff ...
```

## Why not the alternatives

| Chosen | Alternative | Why not |
|---|---|---|
| ICL NOP | more kernel stubs | kernel delivery already `sent=1`; consumer was the wall |
| kernel autoswipe | userland injector | no shell/log tools; signing/entitlements needed |
| `blkdiff`/`blkpatch` | `adb pull` the 16 GiB image | long pulls stalled; moving 244 MiB of diffs is tractable |
| pinned baseline + recipe | copy the upstream tree into the repository | no upstream license; patchset hash keeps it honest |
| `boot_verify` | flash and see | a wrong 128 MiB layout fails silently in LK |
| `boot_layout` for rebuilds | compare image SHA | the original filler was random; layout is the reproducible gate |
