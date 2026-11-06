# 02 — 硬件坐标

[English](../en/02-hardware.md) · **中文**

除标注 **[DTS]**（小米 `ruby-s-oss`）或 **[推断]** 外，均为作者机器实测。
换机时先用 live FDT 复核，不要直接复用。

## CPU

| 项 | 值 | 说明 |
|---|---|---|
| SoC | MediaTek MT6877TT（天玑 1080） | `ruby` |
| 小核 | 6× Cortex-A55，MIDR `0x412fd050` | 最高 2.0 GHz [实测] |
| 大核 | 2× Cortex-A76，MIDR `0x411fd410` | 最高 2.6 GHz [实测] |
| MPIDR | A55 `0x000..0x500`；A76 `0x600,0x700` | Aff1 编号 |
| PSCI | 1.0，`smc` | context id 0 |
| 16K 页 | 两种核都支持 `TGran16` | 不需要 Silver 核 park |
| LSE/LDAPR | 原生支持 | 不需要模拟 |

XNU 跑在 6 个 A55 上（`cpus=6`），A76 暂未使用；16K 页的 XNU 在 A55 上跑，
省掉 topaz 的 Silver 核处理。

## 内存

| 项 | 值 | 说明 |
|---|---|---|
| `/memory` | `0x40000000` + `0x200000000` | 8 GiB [live FDT] |
| MemTotal | 7,734,424 kB | Android 视角 |
| Framebuffer reserved | `0x7ba10000` + `0x1df0000` | `mblock-20-framebuffer` |
| LK 扫描层 | `0x7cdfc000`，pitch **4352** | ovl1/layer0；实际可见层 |
| LK 第二层 | `0x7c406000`，pitch 4320 | ovl0/layer1 |
| DTB（`x0`） | `0x47c80000`，254,232 B | live FDT，`off_struct=0x38` |

以 live FDT/reserved-memory 为准，不要用 DTS 里的占位
`atag,videolfb-fb_base_l`。可见的 LK 层是 `0x7cdfc000`，不是 kernel fb 基址。

## 中断与定时器

| 项 | 值 | 说明 |
|---|---|---|
| GIC | GICv3 | dist `0x0c000000+0x40000` |
| Redistributor | `0x0c040000+0x200000` | stride `0x20000` |
| Timer | `arm,armv8-timer`，13 MHz | `clock-frequency=13000000` |
| 使用的 INTID | VTIMER 27 / PTIMER 30 / SGI 1 | DT PPI 11/14 + 16 |
| GIC sysreg | `ICC_*_EL1` | LK 已启用 GICv3 |

## 存储

| 项 | 值 | 说明 |
|---|---|---|
| UFS host | `11270000.ufshci`，`mediatek,mt8183-ufshci` | IRQ SPI 137 |
| MPHY | `0x11fa0000+0xc000` | |
| 型号 | Kioxia `KM8F9001JM-B813` | 256 GB，UFS 2.2 |
| LUN 0/1 | 各 4 MiB raw | 无文件系统 |
| LUN 2 | 256 GB 用户区 | GPT 与 Android 分区 |
| `boot_a/b` | 各 128 MiB | v2 header，page 2048 |
| `super` | 约 9.1 GB | 动态分区 |
| `userdata` | stock 242 GB | 示例中缩到 208.4 GiB |
| `iosroot` | 示例 17 GiB | HFS+ root；不是 stock 分区 |

XNU UFS 驱动用 LUN 2，GPT header 在 512、entries 在 1024。作者布局把 iOS root
放在 `iosroot`；上游路径用 `userdata`。

## 显示

| 项 | 值 | 说明 |
|---|---|---|
| 面板 | `m16_36_02_0b` | 1080×2400，120 Hz AMOLED |
| DSI | DSI0 `0x14013000`，IRQ 313 | MIPI TX `0x11e50000` |
| DSC | 1080×2400，slice 540×20，128 bpp | `DDP_COMPONENT_DSC0` |
| 面板 GPIO | reset 40，VDDI 108，VDD 167，LED6 | [DTS] |
| iOS 呈现 | 逻辑 1125×2436，面板 1080×2400 | display-scale=3，偏移 22/18 |

## 触摸、按键与电源

| 项 | 值 | 说明 |
|---|---|---|
| 触摸 | Goodix **GT9916R** | SPI3 `0x11013000` |
| IRQ/reset | EINT14（GPIO14，下降沿）/ GPIO15 | DVDD GPIO110；SPI288 父线为 level，映射 RubyGIC INTID 288 |
| 量程 | ABS 10800×24000 | 面板 1080×2400（10×） |
| 固件 | `goodix_firmware_m16_TM.bin` | **TM** 已确认；版本/config 相等时无需主机下载 |
| 驱动 | 0179，原生 EINT14 → 子 controller → oneshot WorkLoop → SPI3 | MT6360 LDO3 1.8 V / LDO2 3.3 V；0085 bit-bang 轮询为历史；见[触摸手册](touch-goodix-9916r.md) |
| 按键 | `mtk-kpd @ 0x10010000` | 电源/音量；音量下 KPD IRQ 走 RubyGIC INTID 138；不是 pwrap 按键 |
| PMIC | pwrap `0x10026000/0x10028000` | MT6359；MT6360 充电；MT6315 SPMI |
| USB | MTU3 `usb0@11201000` | U2/U3 PHY，MT6360 Type-C；未移植 |

## 启动与安全

| 项 | 值 | 说明 |
|---|---|---|
| Bootloader | 小米 LK | 已解锁，`verifiedbootstate=orange` |
| 槽位 | A/B，使用 `_a` | b 槽坏（`hdr_loaded`） |
| Boot header | Android v2，page 2048 | `kernel_addr=0x40080000`，`ramdisk=0x51100000` |
| stock kernel | gzip 16,606,685 | raw 37,449,728，无尾部填充 |
| stock ramdisk | 17,634,771 | Magisk 17,876,407 |
| DTB | `0x20e3800`（Magisk） | MTK magic `d7b7ab1e`，FDT `d00dfeed` |
| AVB0 / AVBf | `0x210e000` / `0x7ffffc0` | 完整 128 MiB 镜像里都要保留 |
| LK fastboot | flash/erase/set_active/oem | **没有 `boot:`** |

## 不要假设

- `fastboot boot` 能用：不能，LK 没有 `boot:`。
- b 槽能用：即使刷已知可启动镜像，也在 `hdr_loaded` 失败。
- `atag,videolfb-fb_base_l` 是最新的：以 live FDT 为准。
- `0x7ba10000` 是可见层：LK 扫描层是 `0x7cdfc000`。
- GPU/Wi-Fi/蓝牙/音频/相机/SEP 可用：都没移植；UI 是软件渲染。
