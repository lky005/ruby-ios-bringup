# Offline image tools

These tools operate on files, never on a device. They are deliberately generic;
offsets, block indices and byte patterns are arguments.

| Tool | What it does | Writes? |
|---|---|---|
| `icl_nop.py` | patch a 4-byte instruction in a raw block or raw image | only with `--apply`, after a backup and SHA checks |
| `dyld_scan.py` | parse Apple's split dyld shared cache and locate a VA | no |
| `boot_verify.py` | print a SWEETXNU-packed boot image's layout and cmdline | no |

## ICL patch

The default is a dry run. It validates the original bytes and optional block
SHA before writing; `--apply` writes a backup, patches the block, fsyncs and
re-reads it.

```sh
# inspect a standalone block
python icl_nop.py --input-block block.bin \
    --in-block-offset 0xF0C --expect-bytes 02255e95 --patch-bytes 1f2003d5

# apply to a raw image, with a backup and both SHA checks
python icl_nop.py --image root.img --block-index 2438140 \
    --in-block-offset 0xF0C \
    --expect-block-sha <original-block-sha> \
    --expect-patched-sha <patched-block-sha> --apply
```

The original 4K block and the patched block used during the bring-up are not
included in the repository. The hashes are recorded in
`docs/records/VERIFICATION.md`.

## dyld scanner

```sh
python dyld_scan.py --cache-dir /path/to/com.apple.dyld \
    --image-name InstalledContentLibrary --va 0x1b11b9f0c
```

This only parses the cache; it does not extract or modify Apple code.

## Boot image verifier

```sh
python boot_verify.py boot.img [base.img]
```

It decompresses the kernel slot, checks the `SWEETXNU` header, prints the
segment/ADT fields and the cmdline, and optionally compares the tail of the
image with a base image.
