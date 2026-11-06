# 06 — 输入：Goodix 触摸、按键与合成上滑

[English](../en/06-input.md) · **中文**

当前 0179 线由 EINT14 硬件边沿经子 EINT controller + 专用 IOWorkLoop
oneshot 驱动真实的 Goodix GT9916R；0085 的 bit-bang/轮询路径保留在下方
作为历史；0084 的合成上滑仍是回退路径和 HID 链路证明。完整的硬件/协议
手册见 [touch-goodix-9916r.md](touch-goodix-9916r.md)。

## 原生 IRQ 触摸（0175–0179）

```text
EINT14（下降沿）
  -> EINT 子 controller（vector = line）
       -> 专用 IOWorkLoop 上的子 IOInterruptEventSource
            -> gt_service_frame()：SPI3 读帧 + HID 提交
            -> service_done()：MASK_CLR + ACTIVE，重开引脚
```

- SPI288 父线是 level，注册为 RubyGIC INTID 288；filter 只做 mask/ACK/
  计数并 raise line 14，不睡眠、不做 SPI/HID。
- 子 action 在 work loop 执行，不在 CPU 中断；命令/诊断在同一
  `IOCommandGate` 串行；没有 `gt_thread`，也没有第二个 SPI3 消费者。
- 脏帧/读帧失败只丢帧并无条件重开线，不会因一次错误进入 STUCK/
  POLL_ONLY；连续 8 次失败做一次 SPI FIFO 复位 + 芯片软握手。注入下观察
  到 `soft reset no-ack`（注入器在 8 连败边界残留 1–2 帧失败），`ok`
  路径未证。
- 无 ESD timer：静默卡低且无新边沿时只能重启。
- 证据：G1–G6；首次 10 min `isr 2381→6004`、`ok=5997`、`fail=7`；约
  5 min 压测 `isr 8672→13282`、`ok=12866`、`fail +9`；1–5 指帧；无
  panic/STUCK/`line=14 active` 重激活。G7（0177 回退）和 G8（USB
  re-plug）按决定取消。

## 真实触摸（0085，历史）

```
内核线程（100 Hz 轮询）
  -> 0x10308 触摸帧（线上 34 字节，数据 26 字节）
  -> head/point checksum，清 sync
  -> sweet_hid_touch(id, down, raw_x/10, raw_y/10)
  -> IOHIDEventService -> backboardd -> SpringBoard
```

驱动做的事：

- 把 MT6360 LDO3（VMC）设为 1.8 V、LDO2（VTP）设为 3.3 V 并使能，
  同时拉高 IOVDD 开关 GPIO110；LK/PMIC 默认是 3.0 V/1.8 V，**只写
  enable 位不够**；
- 复位 GPIO15：低 10 ms、高 100 ms；
- 把 SPI3 的 160–163 切成 GPIO，按 Mode 0、约 250 kHz bit-bang；
- 上报前验证 `dev_confirm`（`0x10000` 写 8×0xAA）和 `0x10014` 版本
  （`BERLIN`、PID `9916R`、U8-LE checksum）；
- 轮询 `0x10308`，校验 8 字节 head 和 point checksum，写 0 清 sync；
  最多上报两指；raw 坐标除以 10（10800×24000 -> 1080×2400），不翻转；
- 手指消失、或连续 50 次坏读时释放。

实机证据：`SWEET GT: BERLIN/9916R ready, 1080x2400`；206 down / 206 up，
40 条 finger-1、84 条 edge；真实底边上滑解锁成功。两指同时按下时
`SweetHIDTouch::touch()` 会把两个 finger 都 append 到同一个 digitizer
collection；用户态 pinch 未单独加日志验证。0085 限制：轮询、无 IRQ/ESD、
最多两指、不做固件/config 下载。0179 线把轮询换成 EINT14（见上）；当前
runs 已记录 1–5 指帧并达到 1–5 指 HID。

## HID 链路

```
SweetHIDTouch::touch()
  -> IOHIDEventService -> IOHIDEventSystem
  -> backboardd -> SpringBoard
```

真实驱动和合成定时器共用这个入口。`touch()` 期望面板像素
（0..1079 × 0..2399），所以喂 `raw/10`。

## 按键（0150 轮询；0169/0175 IRQ）

0150 驱动轮询 MTK KPD 和 MT6359 `TOPSTATUS`（保留为历史；0169 增加音量下
KPD IRQ，0175 迁到 RubyGIC INTID 138）：

- 音量下：KPD `KP_MEM1` bit0（0 = 按下）；
- 电源：`TOPSTATUS 0x2a` bit1；音量上：bit3（低有效、消抖）；
- 20 ms 轮询 + 两次确认；`sweet_hid_key(0/1/2)` -> HID
  `0xe9`/`0xea`/`0x30`；
- 零 PMIC 写；`0x910` 保持 `0x0025`；0155 真机 19 步已覆盖按键；
- 音量下+电源组合 parked；长按电源、音量上+电源可用。

0155 的触摸 LDO 段与电池/probe 共用 I2C5 IOLock；`sweetgt=1` 重新启用
0085 驱动。0179 runs 使用 IRQ 路径（`rubyeint=1`、`rubyeintb1=1`、
`rubykpdirq=1`），并在 G4/G6 覆盖音量下键（G4 19 down/20 up；G6
43/43）。P2 诊断镜像在注明处使用 `sweetgt=0`。

## 边缘位

| 项 | 值 | 说明 |
|---|---|---|
| 起点 Y | `2390` | 底部 48 px 边缘区内 |
| 区域判据 | `y > 2399 - 48` | 置 `kIOHIDDigitizerEventFromEdgeTip` |
| 原因 | UIKit 的 home 手势需要 edge 位 | 否则只是一次拖动 |

0071 加了 edge-tip 位；0084 合成滑动从 y=2390 开始，真实底边上滑同样带
这个位。

## 合成上滑（0084，保留）

| 参数 | 含义 | 0084 值 |
|---|---|---|
| `sweetautoswipe` | 首次延迟 ms；0 关闭 | `90000` |
| `sweetautoswiperetry` | 重试间隔 ms（最小 1000） | `15000` |
| `sweetautoswipeattempts` | 次数（最大 8） | `3` |

0085 的启动 cmdline 去掉了这些参数，使用 `sweetgt=1`。设 `sweetgt=0`
即可关闭 Goodix 驱动，不需要重编。

## 用户态限制

当前 iOS root 没有 `/bin/sh`、`/usr/bin/log`、`launchctl`、`notifyutil`；
`hidutil` 只能读写 HID 属性。因此内核驱动是更小的路径。
