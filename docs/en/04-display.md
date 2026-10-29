# 04 — Display

**English** · [中文](../zh/04-display.md)

The CPU-copy display path is proven for this bring-up: the iOS surface reaches
the panel and the UI refreshes. There is no GPU driver; this is a measured
framebuffer copy, not a general display stack. The remaining black wallpaper is
attributed to PosterBoard `[inferred]`, not to the display path.

## Path

| Stage | Value | Note |
|---|---|---|
| iOS surface | 1125×2436 logical | `display-scale=3`, offsets 22/18 |
| IOMFB service | `AppleCLCD` | IOSurface + IOMobileFramebuffer |
| Copy region | 1080×2400 | surface centre → panel |
| LK scan buffer | `0x7cdfc000`, stride 4352 | actual visible layer |
| Kernel fb/atag base | `0x7ba10000` | not the visible layer |

```
SpringBoard/CoreAnimation -> IOSurface -> IOMFB -> memcpy -> LK fb -> panel
```

The Apple logo is the boot-snapshot surface, not a stale LK frame. The copy is
driven by IOMFB, not by the bootloader after handoff.

## Cache maintenance

| Attempt | Result |
|---|---|
| `flush_dcache64(pa, len, TRUE)` | panic: `phys_to_kv_range: illegal PA: 0x7cdfc000` |
| `flush_dcache64((addr64_t)fPixels, len, FALSE)` + `dsb sy` | works |

The framebuffer is outside the kernel-managed physical range, so a
physical-address flush panics. Flush by kernel VA and `dsb sy`.

## Evidence

- 64×64 magenta at (0,0) and green at centre reached the panel.
- Log: `SWEET FB DBG: ... dst_pa=0x7cdfc000 w=1080 h=2400 ...`.
- `src0/srcc/dst0/dstc = 0xff000000/0xffffffff/...` showed the surface centre
  was the white Apple logo → the displayed image was the boot snapshot.
- The clock refreshed for minutes on the lock screen → a live UI, not a frozen
  first frame.

## Not display

| Symptom | Cause |
|---|---|
| Black wallpaper | PosterBoard `_stateLock_setupSwitcherConfigurationForFirstTime` crash [inferred] |
| Widget `Waiting...` | WidgetKit/chronod/extensions not ready [inferred] |
| Brief white flash top-left on minute refresh | status-bar redraw / surface-present artifact; unresolved |
| Messages red badge | app install/launch issue; not blocking HID |

Do not chase the Apple logo or the panel again; the display path is proven. The
remaining cosmetic issues are userland/extension problems.

## Verification

- `tools/image/boot_verify.py <image>` reports the packed payload and cmdline.
- On the device, the debug markers are the quickest end-to-end check.
- No display tool writes to the device; use the image verifier offline.
