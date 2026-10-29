# 03 — Boot chain and image layout

**English** · [中文](../zh/03-boot-chain.md)

LK accepts a full 128 MiB boot image with the stock kernel stream size.
Everything else is a variation of that recipe.

## LK chain

```
Xiaomi preloader -> LK (unlocked)
  -> read boot_a (Android boot v2, page 2048)
  -> gzip kernel -> 0x40080000
  -> ramdisk -> 0x51100000
  -> MTK DTB header + DTB -> 0x47c80000
  -> jump K64, EL1h, x0 = DTB
```

LK log signatures:

```
booting linux @ 0x40080000, ramdisk @ 0x51100000
[LK]jump to K64 0x40080000
boot linux-64 via EL2, x0=0x47c80000
```

`jump to K64` without `hdr_loaded`/`decompress`/`panic` means the image was
accepted and the payload executed.

## Full 128 MiB layout

| Item | Value | Note |
|---|---|---|
| Partition size | 134,217,728 B | 128 MiB |
| Header | Android v2, page 2048 | `ANDROID!` |
| Kernel stream | 16,606,685 B gzip | exactly the stock size |
| Kernel load | `0x40080000` | |
| Ramdisk | 17,876,407 B (Magisk) | 17,634,771 stock |
| Ramdisk load | `0x51100000` | |
| DTB offset | `0x20e3800` | Magisk layout; stock `0x20a8800` |
| AVB0 | `0x210e000` | |
| AVB footer | `0x7ffffc0` | last 4 KiB of the partition |

A 36.7 MB image leaves a stale/mismatched AVB footer. The full image keeps DTB,
AVB0 and footer at their stock offsets.

## Small payload

1. Take a stock/Magisk full image; decompress the kernel to 37,449,728 B.
2. Keep the ARM64 Image header (`ARM\x64` at raw+0x38).
3. Branch at raw[0:4] to `0x1000` (`0x14000400`).
4. Put the payload at raw+0x1000.
5. Re-gzip to **exactly** 16,606,685 B (FEXTRA padding, no trailing zeros).
6. Write back without moving DTB/ramdisk/AVB.

Success: the panel turns red; LK expdb shows `jump to K64`.

## Shim payload

1. Link the shim at `0x40080000` with its own Linux Image header.
2. Zero the decompressed raw kernel, copy the shim, pad to `_end`.
3. Fill the rest so the gzip stream reaches the stock size; FEXTRA pads to
   exactly 16,606,685.
4. Keep DTB/ramdisk/footer positions.

The early packers are in `src/bringup/`; the 0085/0084 images used the upstream
loader + ADT builder, which is not included as source here.

## FEXTRA detail

- gzip FLG=0x04; XLEN is the pad length.
- The compressed stream must be exactly the stock `kernel_size`.
- No trailing zero bytes.
- Reference: `src/bringup/build_full_a.py`, `build_shim_full.py`.

## Why slot b is abandoned

| Try | Result |
|---|---|
| 4 KB custom image | transfer timeout / `can't find v2 dtb` |
| 18 MB kernel + DTB | `can't find v2 dtb` / `img_loaded` |
| 36.7 MB stock layout | `decompress kernel image fail` |
| 36.7 MB gzip | `hdr_loaded` panic |
| Known-good boot_a image copied to b | **also `hdr_loaded`** |
| Disable vbmeta_b | still `hdr_loaded` |

The b-slot header/AVB path itself is broken. Use `_a` and a known-good full
image to recover.

## Console and watchdog

- Visible LK layer: `0x7cdfc000`, stride 4352; second layer `0x7c406000`.
- Early shims wrote `0x7ba10000` and were invisible; v2 moved to `0x7cdfc000`.
- LK enables MTK TOPRGU at `0x10007000`; disable with `0x22000000`, feed
  `0x10007008 = 1` in spin/panic loops.
