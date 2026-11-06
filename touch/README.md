# 触控 bring-up 实验室

真实触摸已通过 0085 移植并在实机验证（锁屏底边上滑、双指 contact 分发、
edge；用户态 pinch 未单独验证）。当前 0179 线改由 EINT14 原生中断 +
子 controller + oneshot WorkLoop 驱动（1–5 指帧；无 ESD timer）；
0085 的 bit-bang 轮询保留为历史。
0084 的合成上滑证明了
`SweetHIDTouch -> IOHIDEventService -> backboardd -> SpringBoard` 链路；
本目录保留 probe 阶梯、硬件契约和失败记录，完整手册见
[`docs/zh/touch-goodix-9916r.md`](../docs/zh/touch-goodix-9916r.md)。

## 已钉死的硬件

| 项 | 值 | 来源 |
|---|---|---|
| 触控 IC | Goodix GT9916R | [02-hardware](../docs/zh/02-hardware.md#L74) |
| 总线 | SPI3 `0x11013000` | 同上 |
| IRQ / reset | GPIO14 / GPIO15 | 同上 |
| DVDD | GPIO110 | 同上 |
| 量程 | ABS 10800×24000 | 同上 |
| 固件 | `goodix_firmware_m16_TM.bin`（TM 已确认；GVO 未使用） | [contract](contract.md) |
| HID 入口 | `SweetHIDTouch::touch(finger, down, x, y)` | [0084](../patches/0084-ruby-autoswipe.patch#L132) |

**2026-10-22 Android su 取证：** TM、GT9916R/BerlinD、SPI3 5 MHz/CS0、
EINT14 edge、AVDD 3.3 V / IOVDD 1.8 V 已确认；固件版本相等、config 相等。
详见 [contract.md](contract.md)。

**2026-10-22 输入抓取：** `event5` 活跃期约 238 Hz，坐标方向正常，slot 0/1
双指可用；压力/宽度轴声明了但未上报。`touch()` 吃面板坐标
0..1079×0..2399，不是 iOS 逻辑坐标。详见 [contract.md](contract.md)。

**2026-10-22 SPI 长度：** IRQ 线程主循环 **34 + 6 字节**，约 4 ms 一轮；
26/42 字节变体只在双指/慢拖段出现；kworker 每 ~3.07 秒的 9+6 不是主上报。
详见 [contract.md](contract.md)。

**2026-10-22 源码对照（`ruby-s-oss@914ba84`）：** 34 = 8 字节 SPI 前缀
+ 26 字节预读；6 = 5 字节前缀 + 1 字节 sync 清零；26/42 = `touch_num`
为 3/5 时的追加读。BerlinD 没有软复位序列；版本/config 相等时固件更新直接
返回，不写 flash。详见 [contract.md](contract.md) 第 4 节。

**平台寄存器：** SPI3 实际 pin 是 **160-163**，pinmux `0x10005440`
低 16 位写 `0x2222`；SPI3 gate 是 active-low：**CLR `0xa8` bit10 开钟**，
SET `0xa4` 是关钟；MT6360 LDO3/VMC 是 I2C5 `0x64` 寄存器 `0x05` bit6。
详见 [contract.md](contract.md)。

**P0 只读 probe：** 已构建 `<workdir>/touch-p0.img`
（SHA-256 `b5772eef…`），只读 SPI3/pinctrl/clock 状态，不写 MMIO。
源码和构建方式见 [probe/README.md](probe/README.md)。

**危险节点：** 不要 `cat` `fwupdate/goodix_sysfs_fwsize`——会触发
`CFI failure (goodix_sysfs_fwsize_show)` 并让内核 panic/重启。

## 目录

| 路径 | 内容 |
|---|---|
| `android-readonly.md` | Android `su` / TWRP 只读取证；两者差异与命令 |
| `contract.md` | 触控合同模板；把未知项填成有证据的结论 |
| `probe/` | bare-metal touch probe；先 PIO/轮询，不碰 HID |

易变的设备 run card 仍放 `ruby-ios-probes`；本目录只放稳定文档、合同和
probe 源码。

## 五个闸门

| # | 阶段 | 通过条件 | 产物 |
|---|---|---|---|
| 0 | 只读取合同 | 固件变体、复位/供电顺序、SPI 参数、包格式都有日志/DT/源码依据 | `contract.md` 填完 |
| 1 | bare-metal chip ID | 连续多次稳定读到 GT9916R ID | probe 源码 + 屏幕/日志 |
| 2 | bare-metal touch report | 手指按下/抬起，raw x/y 变化 | probe 源码 + 原始包 |
| 3 | XNU 轮询接 HID | 真手指能点按/滑动，能解锁 | XNU 补丁 + run card |
| 4 | IRQ/多点/休眠 | 中断驱动、多点、唤醒后恢复 | 后续 |

## 规则

- **vendor/Linux 驱动只当说明书**：不写新的 Linux input 驱动，不复刻
  `input_dev`/`mt_report`/EINT；只提取硬件时序、SPI 参数、包格式。
- **HID 层不动**：坐标最终调用现有 `SweetHIDTouch::touch()`；先单点，
  后多点。
- **一次只动一个变量**：先只读取证，再 probe，再 XNU；每阶段有独立闸门。
- **不把固件 blob、设备 dump、序列号/IMEI 放进仓库**；只记录文件名、
  hash、来源和脱敏日志。
- **刷 TWRP / `boot_a` 前先备份 0084 和回滚镜像**；TWRP 占 `boot_a`
  （D7），数据只读不等于设备只读。
