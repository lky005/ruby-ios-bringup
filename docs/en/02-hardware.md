# 02 — Hardware

**English** · [中文](../zh/02-hardware.md)

Measured on the author's `ruby` unit unless marked **[DTS]** (Xiaomi
`ruby-s-oss`) or **[inferred]**. Check the live FDT before reusing a value on
another unit.

## CPU

| Item | Value | Note |
|---|---|---|
| SoC | MediaTek MT6877TT (Dimensity 1080) | `ruby` |
| Little cores | 6× Cortex-A55, MIDR `0x412fd050` | up to 2.0 GHz [measured] |
| Big cores | 2× Cortex-A76, MIDR `0x411fd410` | up to 2.6 GHz [measured] |
| MPIDR | A55 `0x000..0x500`; A76 `0x600,0x700` | Aff1 numbering |
| PSCI | 1.0, `smc` | context id 0 |
| 16K pages | both core types support `TGran16` | no Silver-core parking |
| LSE/LDAPR | native | no emulation needed |

XNU runs on the six A55s (`cpus=6`). The A76 pair is not used yet; running
16K-page XNU on A55 avoids the topaz Silver-core workaround.

## Memory

| Item | Value | Note |
|---|---|---|
| `/memory` | `0x40000000` + `0x200000000` | 8 GiB [live FDT] |
| MemTotal | 7,734,424 kB | Android view |
| Framebuffer reserved | `0x7ba10000` + `0x1df0000` | `mblock-20-framebuffer` |
| LK scan buffer | `0x7cdfc000`, pitch **4352** | ovl1/layer0; actual visible layer |
| LK second layer | `0x7c406000`, pitch 4320 | ovl0/layer1 |
| DTB passed in `x0` | `0x47c80000`, 254,232 B | live FDT, `off_struct=0x38` |

Use the live FDT/reserved-memory, not the DTS placeholder
`atag,videolfb-fb_base_l`. The visible LK layer is `0x7cdfc000`, not the kernel
fb base.

## Interrupts and timers

| Item | Value | Note |
|---|---|---|
| GIC | GICv3 | dist `0x0c000000+0x40000` |
| Redistributor | `0x0c040000+0x200000` | stride `0x20000` |
| Timer | `arm,armv8-timer`, 13 MHz | `clock-frequency=13000000` |
| Used INTIDs | VTIMER 27 / PTIMER 30 / SGI 1 | DT PPI 11/14 + 16 |
| GIC sysreg | `ICC_*_EL1` | LK has already enabled GICv3 |

## Storage

| Item | Value | Note |
|---|---|---|
| UFS host | `11270000.ufshci`, `mediatek,mt8183-ufshci` | IRQ SPI 137 |
| MPHY | `0x11fa0000+0xc000` | |
| Device | Kioxia `KM8F9001JM-B813` | 256 GB, UFS 2.2 |
| LUN 0/1 | 4 MiB raw each | no filesystem |
| LUN 2 | 256 GB user area | GPT and Android partitions |
| `boot_a/b` | 128 MiB each | v2 header, page 2048 |
| `super` | ~9.1 GB | dynamic partitions |
| `userdata` | 242 GB stock | shrunk to 208.4 GiB in the example |
| `iosroot` | 17 GiB example | HFS+ root; not a stock partition |

The XNU UFS driver uses LUN 2, GPT header at 512 and entries at 1024. The
author's layout puts the iOS root on `iosroot`; the upstream path uses
`userdata` instead.

## Display

| Item | Value | Note |
|---|---|---|
| Panel | `m16_36_02_0b` | 1080×2400, 120 Hz AMOLED |
| DSI | DSI0 `0x14013000`, IRQ 313 | MIPI TX `0x11e50000` |
| DSC | 1080×2400, slice 540×20, 128 bpp | `DDP_COMPONENT_DSC0` |
| Panel GPIO | reset 40, VDDI 108, VDD 167, LED6 | [DTS] |
| iOS presentation | 1125×2436 logical, 1080×2400 panel | display-scale=3, offsets 22/18 |

## Touch, keys and power

| Item | Value | Note |
|---|---|---|
| Touch | Goodix **GT9916R** | SPI3 `0x11013000` |
| Touch IRQ/reset | EINT14 (GPIO14, edge falling) / GPIO15 | DVDD GPIO110; SPI288 parent is level and maps to RubyGIC INTID 288 |
| Touch range | ABS 10800×24000 | panel is 1080×2400 (10×) |
| Touch firmware | `goodix_firmware_m16_TM.bin` | **TM** confirmed; no host download when version/config match |
| Touch driver | 0179, native EINT14 → child controller → oneshot WorkLoop → SPI3 | MT6360 LDO3 1.8 V / LDO2 3.3 V; 0085 bit-bang poll is historical; see [touch manual](touch-goodix-9916r.md) |
| Keys | `mtk-kpd @ 0x10010000` | power/volume; volume-down KPD IRQ on RubyGIC INTID 138; not pwrap keys |
| PMIC | pwrap `0x10026000/0x10028000` | MT6359; MT6360 charger; MT6315 SPMI |
| USB | MTU3 `usb0@11201000` | U2/U3 PHY, MT6360 Type-C; not ported |

## Boot and security

| Item | Value | Note |
|---|---|---|
| Bootloader | Xiaomi LK | unlocked, `verifiedbootstate=orange` |
| Slots | A/B, use `_a` | slot b is broken (`hdr_loaded`) |
| Boot header | Android v2, page 2048 | `kernel_addr=0x40080000`, `ramdisk=0x51100000` |
| stock kernel | gzip 16,606,685 | raw 37,449,728, no trailing pad |
| stock ramdisk | 17,634,771 | Magisk 17,876,407 |
| DTB | `0x20e3800` (Magisk) | MTK magic `d7b7ab1e`, FDT `d00dfeed` |
| AVB0 / AVBf | `0x210e000` / `0x7ffffc0` | keep both in a full 128 MiB image |
| LK fastboot | flash/erase/set_active/oem | **no `boot:`** |

## Do not assume

- `fastboot boot` works: it does not; LK has no `boot:`.
- Slot b is usable: it fails at `hdr_loaded` even with a known-good image.
- `atag,videolfb-fb_base_l` is current: use the live FDT.
- `0x7ba10000` is the visible layer: the LK scan buffer is `0x7cdfc000`.
- GPU/Wi-Fi/Bluetooth/audio/camera/SEP exist: none are ported; the UI is
  software-rendered.
