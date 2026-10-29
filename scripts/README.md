# Scripts

| Script | Purpose |
|---|---|
| `fetch-base.sh` | clone a pinned `ios-topaz` baseline for inspection |
| `verify-local.py` | host-side syntax, ICL round-trip, PII/secret and optional patch/boot checks |
| `check-bundle.py` | compare kernel/boot/root/ICL/cmdline/shim/payload against the success bundle |
| `build-payload.sh` | fetch upstream payload tools and build a SWEETXNU payload |
| `test-pipeline.sh` | host-only payload → deterministic pack → layout test |

## Fetch the baseline

The upstream tree is not copied into this repository. Choose the fork and commit you use:

```sh
BASE_REPO=https://github.com/<owner>/ios-topaz.git \
BASE_REF=<commit> ./scripts/fetch-base.sh upstream
```

The script refuses to overwrite an existing destination. It does not copy the
patches; copy `patches/` into the fetched tree's `xnu/patches/` when building.

## Local verification

```sh
python scripts/verify-local.py
```

Optional checks:

```sh
python scripts/verify-local.py \
    --icl-orig /path/to/icl_block_orig.bin \
    --icl-patched /path/to/icl_block_patched.bin \
    --xnu-tree /path/to/patched/xnu \
    --boot-image /path/to/boot.img
```

The ICL block options expect the real 4K blocks from your own image; they are
not included. The `--xnu-tree` checks are informational because the tree state
depends on which upstream patches are already applied.

No check writes to the device or modifies the images it is given. The ICL test
writes only to a temporary directory.

## Host pipeline

The payload/pack/layout stages use <1 GiB artifacts and never touch the root
image. The shim and ADT are external; the upstream payload tools are fetched at
the pinned baseline commit.

```sh
sh scripts/build-payload.sh --kernel <kernel> --adt <adt> \
  --cmdline-file config/0084-boot.cmdline --out <payload.bin>

python tools/image/pack_boot.py --base <magisk.img> --shim <Image> \
  --payload <payload.bin> --out <boot.img>

python tools/image/boot_layout.py --image <boot.img> \
  --config config/0084.env --payload <payload.bin> --base <magisk.img>
```

`--golden <0084.img>` is optional; the config mode checks pinned header/ADT/
cmdline/shim/payload values without the golden image.

For a strict host bundle:

```sh
python scripts/check-bundle.py --strict ...   # kernel/boot/shim/payload/base/cmdline
python scripts/check-bundle.py --strict --require-root ...  # also root/ICL
```

`--require-root` reads the root image for a SHA check; it does not modify it.

The `host-checks` workflow runs `verify-local.py` and compiles the TWRP tools
on Ubuntu. It does not need the 16 GiB root.

Or run all three:

```sh
sh scripts/test-pipeline.sh --base <magisk.img> --kernel <kernel> \
  --adt <adt> --shim <Image> --golden <0084.img>
```

The packer uses a deterministic filler (seed `0x84`), so the rebuild is stable
(`a0ce0fe1...` for the 0084 inputs). The original image SHA `94c639d1...`
cannot be byte-reproduced because it used `os.urandom`; `boot_layout.py` is the
gate for a rebuilt image.

## Bundle check

Before flashing, compare the artifacts against `config/0084.env`:

```sh
python scripts/check-bundle.py --kernel <kernel> --boot <boot.img> \
  --root <root.img> --icl-orig <orig.bin> --icl-patched <patched.bin> \
  --cmdline <cmdline.txt>
```

Missing files are reported as skipped. Any mismatch means a different
configuration, not a covered reproduction. Device-baseline hashes are not used.
