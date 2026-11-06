# 01 — Architecture

**English** · [中文](../zh/01-architecture.md)

The project is a chain of small replacements, not a single kernel port. This
page places every component and shows where the project's delta sits.

## Boot chain

```
Xiaomi preloader
  -> LK (unlocked)
     -> boot_a: Android boot v2 image, 128 MiB
        -> kernel slot: gzip stream, exactly 16,606,685 bytes
           -> shim/loader (raw AArch64) at 0x40080000
              -> XNU 8796 + ADT + boot args
                 -> UFS LUN 2 -> HFS+ root (iosroot)
                    -> dyld + launchd -> lsd -> backboardd -> SpringBoard
                       -> display: IOSurface/IOMFB -> LK framebuffer
                       -> input:   SweetHID -> IOHIDEventService
```

LK has no `boot:` command, so every experiment is flashed to `boot_a`. The
128 MiB image keeps the DTB, AVB0 and AVB footer at their stock offsets,
avoiding an `hdr_loaded` rejection.

## Layers

| Layer | Component | Project delta |
|---|---|---|
| Bootloader | Xiaomi LK | none; only `boot_a` is written |
| Payload | shim/loader | early `src/bringup`; upstream loader for 0084 |
| Kernel | XNU 8796 | patches 0080/0085 (real touch), 0156-0179 (HAL/USB/battery/native IRQ); 0084 previous; 0081–0083 historical |
| Root | HFS+ in `iosroot` | pulled v14 + seed; not in the repo |
| Userland | iOS 16.7.16 | ICL 4-byte NOP |
| Display | IOSurface/IOMFB | 0081 debug path |
| Input | SweetHID | real Goodix touch driven by native EINT14 since 0179 (0085 bit-bang poll historical); 0084 autoswipe retained |

## The three walls

1. **Image layout.** LK accepts a full 128 MiB image with the stock kernel
   stream size; a 36.7 MB image leaves a mismatched AVB footer.
2. **Display.** The visible buffer is `0x7cdfc000`, pitch 4352; a physical-
   address cache flush panics, a kernel-VA flush works.
3. **Userland.** lsd's first-boot journal recovery waits on a MobileGestalt
   consumer; the kernel notification was already delivered. The ICL NOP
   bypasses the consumer, not the kernel.

## Repository boundary

The repo owns the delta, the tools and the evidence. It does not own Apple's
userland, the iOS root, the boot images or the upstream baseline.
