# 12 — USB 上位机通道：测试条件、驱动绑定与安全调试

**中文** · [English](../en/12-usb-host.md)

> 状态标签沿用仓库 README：**[measured]**、**[DTS]**、**[inferred]**、
> **[historical]**。没有来源的数字就是 bug。本页说明如何操作该通道，
> 不是 host 侧 XACT 的修复方案。

## 已验证（2026-10-30）[measured]

- 内核 0143（patchset `f47f4c19...`，139 文件；CI `41022192026`；
  exec-data `6fa65088...`）以 USB 2.0 设备模式运行：vendor-specific
  设备 `1209:0002`，一个 bulk OUT（`0x02`，64 B MPS）和一个 bulk IN
  （`0x82`，512 B MPS）。
- 枚举、SET_CONFIGURATION、High-Speed 全绿；内核每个 GPD 发一帧日志：
  16 B 头 + 最多 495 B 文本 = 511 B（比 512 B MPS 少 1 字节，保证
  每个 GPD 以 short packet 结束）。
- **host 侧首会话 XACT 仍未闭环**。一次会话送出可变帧数（实测 0–54；
  0 表示 IN pipe 已被 halt），随后 IN URB 以 `0xC0000011` 完成并触发
  `ABORT_PIPE`。EP0 在枚举期或 abort 后也可能 XACT。设备可能保持
  枚举，也可能掉链；一旦 `NO_DEVICE`，物理重启是可靠恢复手段。
- 下面的上位机软件与测试条件就是 0143/0150/0151 实测使用的参考。

## 测试条件

### 设备侧 [measured]

- MT6877，USB 2.0 High-Speed，由上位机端口总线供电。
- vendor-specific 接口，VID:PID `1209:0002`，单个配置。
- bulk OUT `0x02`：64 B MPS；bulk IN `0x82`：512 B MPS。
- 日志帧 511 B；环 64 个 GPD，最多 63 个在飞；reset/rearm 路径在
  停 QMU 后重置 TX 环。
- 内核 USB 窗口 30 s（`rubyusb_window_ms=30000`）；命令通道每次
  接收一行文本（`help`、`stat`、`ring`、`echo`）。

### 上位机侧 [measured]

- Windows 11（`10.0.26300`，x64），AMD USB4 平台。
- AMD USB 3.10 xHCI 控制器；USB 2.0 路径使用 `1022:15b9`。实测过
  两种物理连接：
  - USB4 Type-C 口 + C-to-C（CC）线；
  - USB-A 口 + A-to-C（AC）线。
- 两种连接都出现相同的首会话 XACT。A 口/AC 线三次 fresh boot 分别
  送出 13、7、23 帧，其中一次掉链；更早在 CC/Type-C 口上的
  0142/0143 运行跨 boot 送出 2、3、9、15、27、54 帧。样本量小：
  只能说明**线/口不是唯一根因**，不能说明两种链路等价。
- 手机由上位机端口供电；这些测试没有外接 AC 充电器/适配器。充电器
  + 数据同时连接的场景未覆盖。
- 上位机软件：Python 3.x + `pyusb` + `libusb-package`（WinUSB
  后端）。EP0 控制请求超时 3 s；EP2 读轮询 200 ms；正常会话 5 ms
  paced；burst 复现时 pacing=0。

## 驱动绑定 [measured] / [inferred]

设备是 vendor-specific class `0xFF`，应绑定 WinUSB 并通过 libusb
打开。不要绑定 CDC/串口驱动：如果 `1209:0002` 出现 COM 口，说明
绑定错了，上位机工具会打不开设备。

通用绑定步骤（工具名只是示例，本仓库不附带）：

1. 为 `1209:0002` 安装 WinUSB（例如 Zadig：Options -> List All
   Devices -> 选 `ruby USB P2`（1209:0002）-> WinUSB -> Replace
   Driver）。
2. 重新插拔手机，用
   `python tools/host/ruby_usb_host.py status` 验证。
3. 如果以前绑定过串口/CDC，先移除对应 COM 设备；不要为了“让它出现”
   随便安装不相关的 CDC INF。

注意：

- `pnputil /enum-devices /connected` 的输出是本地化的。按
  `VID_1209&PID_0002` 行匹配，不要解析英文字段名。
- 实例 ID 是位置相关的；重启后遗留 phantom 条目是正常的。匹配
  当前present 的实例，不要硬编码序列号或位置。
- 本仓库不附带 INF 或驱动二进制。
- `pnputil /restart-device` 只在设备仍然枚举时可用（需管理员）。
  它可能重新枚举并允许新会话，也可能把设备弄掉；它不是
  `NO_DEVICE` 的恢复手段。

## 安全调试（该做 / 不该做）[measured]

**该做**

- 同一时间只跑一个上位机工具。EP2 OUT 是单写者命令通道，IN 读取
  需要安静的总线。
- EP0 超时保持 3 s，失败后退避重试。EP0 有会话相关噪声：同一会话
  第一次读可能成功、后续间歇 EPIPE；重连是正常操作。
- EP2 用 512 B 缓冲读；校验 16 B 头和序号。0143 正常帧 511 B；
  最后一帧更短是合法的。
- 长日志用 5 ms paced 读；只有复现 XACT 时才用 burst（`--pace-ms 0`）。
- EPIPE/XACT 时停止 IN 读取，保留 EP0 做诊断。`claim_interface(0)`
  之后单次 `clear_halt(0x02)` 可以恢复被 halt 的 OUT 管道；做一次，
  不要循环。
- 设备消失（`NO_DEVICE`）就停下，物理重启手机。
- 做线/口 A/B 时每个条件跑多次 fresh boot；单次会话不能当稳定性结论。

**不该做**

- 不要紧循环 clear_halt，不要反复清 EP2 IN。这两者实测都会把设备
  打下总线。
- 不要循环 `pnputil /restart-device`；设备已经消失时它帮不上忙。
- 不要在 IN 排空时发命令；不要让两个进程同时写 EP2。
- 不要连续轰 EP0；EP0 噪声是正常的，重试越多越糟。
- 不要通过 0x2C 读任意 MMIO。它只接受白名单映射；区外返回 STALL。
  不要扫 MTU3 FIFO0（`0x11201300`）或其他数据口：读操会弹出端点
  数据。
- 不要把 `0x22` 的 `inflight`/`enq`/`deq` 当完整计数；它们是 4 位
  截断。用 `outstanding = push_seq - txdone`。
- 不要凭一次线/口试验把 XACT 归因于某根线；CC 和 AC 两种连接都
  出现。
- 不要在会话进行中把 AC 充电器热插到数据口；该组合未测试。

## 上位机工具参考

稳定参考工具已放在
[`tools/host/ruby_usb_host.py`](../../tools/host/ruby_usb_host.py)；
依赖和输出说明见 [`tools/host/README.md`](../../tools/host/README.md)。
EP0 只读；唯一的设备写是 EP2 OUT 命令行和可选的单次 `--pcycle`
重启。

```sh
python tools/host/ruby_usb_host.py status
python tools/host/ruby_usb_host.py cmd "help" --drain-secs 3
python tools/host/ruby_usb_host.py cmd "help" --drain-secs 3 --pace-ms 0
python tools/host/ruby_usb_host.py watch --pace-ms 5 --log session.log
```

- `status`：读 `0x27`（EP0 计数）、`0x23`（RX 诊断）、`0x2B`
  （日志长度）以及 `EP_RST`/`TX2CSR0`/`TQCSR2`/`TQCPR2`。
- `cmd`：向 EP2 OUT 写一行，并在指定时间内排空 EP2 IN；设备以
  日志/命令帧回应。
- `watch`：持续 paced 会话；EPIPE 后 IN 读取停止但 EP0 仍可用；
  设备重新出现时退避重连。
- `--pcycle`：仅对“仍枚举但僵死”的设备做最多一次
  `pnputil /restart-device`。需要提权；只作最后手段。

## 协议细节 [measured]

### EP0 vendor 请求

| 请求 | 方向 | 用途 |
|---|---|---|
| `0xC0/0x21` | IN | 状态：`push_seq`、enq nibble、TX busy/ready、stall 位、`TQCSR2`、`TX2CSR0`、QISAR/TQERR |
| `0xC0/0x22` | IN | 队列诊断：`txcpr`、HWO 计数、`inflight`/`enq`/`deq` nibble、`txdone`、recoveries、QISAR0 |
| `0xC0/0x23` | IN | RX 诊断：packets、bytes、ZLP、last length、CRC/errors、RQ CSR |
| `0xC0/0x27` | IN | EP0 计数：setups、tx packets、data ends、sent stalls、bus resets、cfg/ready |
| `0xC0/0x2A` | IN | 按字节偏移读日志窗口 |
| `0xC0/0x2B` | IN | 日志总字节数（64 位） |
| `0xC0/0x2C` | IN | 读一个 32 位 MMIO 字（仅白名单映射） |
| `0x40/0x2D` | OUT | 写一个 32 位 MMIO 字；需 `rubyprobe=1`；**参考工具不使用** |

### 帧与环

- 一帧 = 16 B 头 + 最多 495 B 文本 = 511 B。
- 头里的序号是 offset 0 的 16 位值；文本从 offset 16 开始。
- 槽间距 512 B；512 B 槽不跨 16 KiB 页，64 B GPD 描述符不跨
  64 B cache line。TX 环 64 个 GPD，最多 63 个在飞。
- 每个 GPD 都是 short packet，这是 QMU 报 TX done 的前提。整 512 B
  满包不是同一回事，早期实验已否决。

### `0x22` 打包

`v[2]` 打包：`hiar[3:0]`、HWO 计数 `[15:8]`、`inflight[3:0]`（bit 16）、
`enq[3:0]`（bit 20）、`deq[3:0]`（bit 24）。`v[3]` 是 `txdone`，
`v[4]` recoveries，`v[5]` QISAR0。内核用 4 位字段，所以上位机必须用
`outstanding = push_seq - txdone` 推导；参考工具同时打印 nibble 和
推导值。

### `0x2C` 可读范围

| 映射 | 范围 | 说明 |
|---|---|---|
| IFRAO | `0x10001000`-`0x10001fff` | 时钟门控状态；只读用途 |
| GPIO | `0x10005000`-`0x10005fff` | pin mux/dir/out |
| MTU3 | `0x11201000`-`0x11203fff` | MAC；**FIFO0 `0x11201300` 不可读** |
| IPPC | `0x11203e00`-`0x11203eff` | 被 MTU3 映射覆盖 |
| PHY | `0x11e40000`-`0x11e41fff` | U2/U3 SIF；驱动只映射 0x2000 |

区外地址返回 STALL，不会 fault。APMIXED/topckgen（USB PLL/时钟）
在 0143 里**没有映射**，所以 0x2C 读不到；要读必须先加内核映射。

### 未闭环故障 [measured]

- 首会话：一条命令（`help`）后送出可变数量的 511 B 帧（实测 0–54；
  0 表示 IN pipe 已 halt），随后 IN URB 以 `0xC0000011`
  （`USBD_STATUS_XACT_ERROR`）完成并触发 `ABORT_PIPE`。
- abort 时设备侧 QMU active、环满（63 outstanding、`hwo=63`）；
  QISAR0/TQERRIR0 为零。不是环空或坏包。
- EP0 在枚举期和 abort 后也可能 XACT；Windows 可能发
  `SYNC_RESET_PIPE_AND_CLEAR_STALL`，设备可能掉链。根因仍未闭环，
  0143 内核没有修复它。

## 证据与边界

- 构建：CI `41022192026`；patchset `f47f4c19...`（139 文件）；
  kernel full `d2eae74d...`、exec-data `6fa65088...`；镜像
  `5b6b8411...`（`config/0143.env`）。
- 设备运行：2026-10-30，作者的上位机，CC 和 AC 两种连接；样本量小。
- 不公开日志、镜像或设备标识。以上数字只在指定构建上实测；新构建
  必须重新测量。
- 只有硬件 USB 分析仪/示波器能观察总线级 CRC 或 480 MHz 抖动；
  0x2C 寄存器读不能证明或否定它。
