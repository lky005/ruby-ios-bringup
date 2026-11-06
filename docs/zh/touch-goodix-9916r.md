# Goodix GT9916R 触摸手册

[English](../en/touch-goodix-9916r.md) · **中文**

本文记录 `ruby` / MT6877 上 Goodix GT9916R 的硬件契约、上电与协议、
bare-metal probe 的结论、XNU 驱动实现、失败路径和复现方法。所有寄存器
和数据都来自 live FDT、Android 运行时、vendor 源码或实机 probe；证据等级
在文中标出。设备序列号、个人路径和完整日志不进入本仓库。

## 1. 身份与契约

| 项 | 值 | 证据 |
|---|---|---|
| 面板 | `m16_36_02_0b`，1080×2400 | `/proc/cmdline` |
| TP 变体 | **TM**（不是 GVO） | Android dmesg |
| 触控 IC | Goodix **GT9916R**，BerlinD | dmesg |
| ROM PID / patch PID | `BERLIN` / `9916R` | `0x10014` 读出 |
| VID / sensor | `00 80 02 64` / `255` | dmesg 与 `0x10014` |
| 固件 | `goodix_firmware_m16_TM.bin`，223,744 B，SHA-256 `4a3baefe…379424d7` | vendor 固件 |
| config | `goodix_cfg_group_m16_TM.bin`，1,421 B，SHA-256 `8974708b…750121db` | vendor 固件 |
| 触摸输入 | ABS 10800×24000，10 槽 | `/dev/input/event5` |
| 主机下载 | 版本/config 相等时**不下载** | vendor `goodix_fw_update_proc()` |

固件和 config 的内容不进入仓库，只记录文件名和 hash。

## 2. 硬件连接

| 信号 | MT6877 | 说明 |
|---|---|---|
| SPI3 | `0x11013000` | `mediatek,mt6765-spi`，CS0，Mode 0，8-bit |
| SPI 引脚 | GPIO **160/161/162/163** | MO / MI / CSB / CLK，function 2 |
| 触摸 IRQ | GPIO14，EINT14 | 下降沿；第一版驱动**不使用**，改为轮询 |
| 复位 | GPIO15 | 低有效；低 10 ms、高 100 ms |
| IOVDD 开关 | GPIO110 | 高=开；`ts_dvddenable` |
| AVDD | MT6360 **LDO2 / VTP** | 3.3 V；EN `0x11` bit6，VOUT `0x15` |
| IOVDD | MT6360 **LDO3 / VMC** | 1.8 V；EN `0x05` bit6，VOUT `0x09` |
| I2C5 | `0x11d00000`，MT6360 slave `0x64` | SCL GPIO132，SDA GPIO133 |

`ts_spimode` 的 pinmux 原始值是 `0xa002/0xa102/0xa202/0xa302`：高字节
`0xA0..0xA3` 就是 GPIO 160..163，低字节 `2` 是 function 2。

## 3. 上电与复位

### 3.1 MT6360 LDO 的 CRC8 访问

MT6360 的 LDO 不是普通单字节寄存器，而是 **CRC8 保护的 SMBus block**：

- 写：`START, addr<<1, reg&0x3f, value, crc, dummy0, STOP`；
- 读：`START, addr<<1, reg, repeated START, addr<<1|1, value+ACK, crc+NACK, STOP`；
- CRC8：poly `0x07`、init `0`、MSB-first，覆盖
  `[addr<<1, reg&0x3f, value]`；读方向地址是 `addr<<1|1`。

CRC 不匹配必须 abort，不能继续写。

### 3.2 默认电压的坑（本次 bring-up 的根因）

Android 早期 dmesg：

```
vtp: Bringing 1800000uV into 3300000-3300000uV
VMC: Bringing 3000000uV into 1800000-1800000uV
```

即 LK/PMIC 默认 **VMC=3.0 V、VTP=1.8 V**，Android 启动后才改成
1.8 V/3.3 V。只写 enable 位会让 AVDD 欠压，芯片完全不启动；这也是
P1f/P1g 一直读到全 0 的原因。正确做法是显式写 VOUT：

- LDO3 `0x09 = 0x3a`（selector `0x3a..0x40` = 1.8 V）；
- LDO2 `0x15 = 0xd0`（selector `0xd0..0xd9` = 3.3 V）。

P1f/P1g 在写 VOUT 之前就使能了电源，芯片短暂经历过 VMC 3.0 V；它没有
损坏，但不要故意重复：应在断电状态写 VOUT、回读，然后再使能。

### 3.3 上电顺序

```
读 EN/VOUT（CRC8）
disable LDO3/LDO2（清 bit6） -> 20 ms
写 VOUT 0x3a/0xd0，回读确认
IOVDD GPIO110 高 -> 3 ms
enable LDO3 -> 30 ms
enable LDO2 -> 15 ms
SPI 引脚切 GPIO、空闲 CS 高/CLK 低
reset15 低 10 ms -> 高 100 ms
dev_confirm -> 版本校验 -> 轮询
```

enable 后 EN 寄存器通常从 `0x80` 变成 `0xC4`（bit6=1）；bit2 是只读状态，
RMW 时保留即可。

## 4. Pinmux / GPIO 寄存器

MTK pinctrl 有两套编号，容易混：

- **DIR/DO/DI** 按 32-pin bank：bank `n` 的偏移是
  `DIR=0x000+n*0x10`、`DO=0x100+n*0x10`、`DI=0x200+n*0x10`；
- **mode** 按 8-pin group：`0x300+group*0x10`，每个 pin 4 bit。
  group = pin/8，不是 bank 号。

| 功能 | pin | bank | mode 寄存器 | DIR/DO/DI |
|---|---|---|---|---|
| I2C5 SCL/SDA | 132/133 | 4 | `0x400` bits16–23 | `0x040/0x140/0x240` |
| SPI3 MO/MI/CS/CLK | 160–163 | 5 | `0x440` bits0–15 | `0x050/0x150/0x250` |
| reset | 15 | 0 | `0x310` bits28–31 | `0x000/0x100/0x200` |
| IOVDD | 110 | 3 | `0x3d0` bits24–27 | `0x030/0x130/0x230` |

SPI 位：MO=bit0、MI=bit1、CS=bit2、CLK=bit3；I2C 位：SCL=bit4、
SDA=bit5；reset=bit15；IOVDD=bit14。

注意：

- **mode 的 `0x400/0x440` 是 group16/group20**，不是 bank4/bank5；
- MTK clock gate 是 active-low：CLR `0x100010a8` bit10 开钟、SET
  `0x100010a4` bit10 关钟，STA `0x100010ac` bit10=1 表示 gated；本驱动用
  bit-bang，不依赖 SPI3 控制器时钟；
- CPOL/CPHA 在 `SPI_CMD` bit8/9；`CFG0=0x3F003F` 是 CS setup/hold 时序，
  不是 mode 3；
- I2C/SPI 线是开漏/外部上拉，释放时把 DIR 设为输入。

## 5. SPI 协议（BerlinD）

### 5.1 帧格式

- Mode 0（CPOL=0、CPHA=0），8-bit，MSB first，CS 低有效；
- 写前缀 **5 字节**：`0xF0 + addr(4, BE)`，后接数据；
- 读前缀 **8 字节**：`0xF1 + addr(4, BE) + 0xFF×3`，后接数据；
  数据阶段 MOSI 发 0；
- bit-bang 半周期 2 µs（约 250 kHz）；控制器标称 5 MHz。

### 5.2 dev_confirm 与版本

- `dev_confirm`：向 `0x10000` 写 8×`0xAA`，回读 8 字节比较；
  vendor 最多 3 次、间隔 5 ms。
- 版本：读 `0x10014` 共 28 字节：

| 偏移 | 字段 |
|---|---|
| 0–5 | ROM PID，`BERLIN` |
| 6–8 | ROM VID |
| 9 | reserved |
| 10–17 | patch PID，`9916R` |
| 18–21 | patch VID，`00 80 02 64` |
| 22 | reserved |
| 23 | sensor id，`0xFF` |
| 24–25 | reserved |
| 26–27 | U8-LE checksum |

校验：`sum(data[0..25]) & 0xffff == data[26] | data[27]<<8`。

### 5.3 触摸帧

触摸数据地址 `0x10308`。预读 26 字节（线上 34）：

| 偏移 | 含义 |
|---|---|
| 0 | event；`0x80` = `GOODIX_TOUCH_EVENT` |
| 1 | 保留 |
| 2 | `touch_num = value & 0x0f` |
| 3–5 | 保留 |
| 6–7 | head checksum：`sum(data[0..5]) & 0xffff` |
| 8–15 | point 0 |
| 16–23 | point 1 |
| 24–25 | point checksum（1 点）/ 32–33（2 点） |

point 8 字节：`[0]` 高 nibble id、低 nibble 类型（1/3 是笔）；
`[2..3]` x LE16；`[4..5]` y LE16；`[6..7]` w。
point checksum 覆盖 `data[8 .. 8+n*8-1]`。

读完有效帧后向 `0x10308` 写 1 字节 0 清 sync（线上 6 字节）。
`touch_num > 2` 时 vendor 会从 `0x10308+26` 追加读；第一版驱动直接丢弃并
清 sync。

### 5.4 控制器路径的 FIFO 坑

MTK SPI 控制器 FIFO 只有 32 字节，而 34 字节预读必须用 DMA 或
32+2 pause/resume。P1f 用 PIO 时把 13 字节写命令按 4 字节整字压了 16 字节，
控制器只移出 13 字节，**FIFO 剩 3 字节**；下一次读命令先发出 `00 00 00`，
读前缀整体错位，于是“写成功、读全 0”。vendor 在每次 CS 释放时调用
`mtk_spi_reset()`（`SPI_CMD_RST`）清 FIFO；后续若改用控制器，必须在传输
前后清 FIFO，或直接用 DMA。当前 XNU 驱动用 bit-bang，绕开了这个坑。

## 6. XNU 驱动（0085 轮询；0179 原生 EINT）

> 下表描述历史 0085 轮询驱动。当前 0179 线保留相同上电/协议代码，但由
> EINT14 硬件边沿服务触摸帧；见 §6.1。



| 项 | 值 |
|---|---|
| 文件 | `bsd/dev/sweet_goodix_spi.c` |
| 启动 | `sweet_ufs.c` 调用 `sweet_goodix_spi_init()` |
| boot arg | `sweetgt=1`（默认开），`sweetgt=0` 关闭 |
| 构建 | `bsd/conf/files` 加一行 |
| MMIO | `ml_io_map(0x10005000, 0x1000)` |
| 线程 | `kernel_thread_start()`，初始化失败则退出 |
| 轮询 | 读 34 字节 + 清 sync，约 8 ms 睡眠 -> ~100 Hz |
| 上报 | `sweet_hid_touch(id, down, raw/10, raw/10)` |
| 释放 | 手指消失、`n=0` 帧、连续 50 次坏读 |
| 限制 | ≤2 指、无 IRQ/ESD、无固件下载 |

上电/协议逻辑与 bare-metal probe 完全一致；XNU 下 MMU 打开，不再有
probe 的 Device-memory 非对齐访问限制。

### 6.1 原生 EINT 服务（0179）

```text
EINT14（下降沿）
  -> EINT 子 controller（vector = line）
       -> 专用 IOWorkLoop 上的子 IOInterruptEventSource
            -> gt_service_frame()：SPI3 读帧 + HID 提交
            -> service_done()：MASK_CLR + ACTIVE，重开引脚
```

- SPI288 父线是 level，注册为 RubyGIC INTID 288；filter 只做 mask/ACK/
  计数并 raise line 14。
- 子 action 拥有 SPI3/HID；命令/诊断在同一 `IOCommandGate` 串行；
  `gt_thread` 已删除，没有第二个消费者。
- 读帧失败只丢帧并重开线；连续 8 次失败做一次 SPI FIFO 复位 + 芯片软
  握手。注入下记录到 `soft reset no-ack`（注入器在边界残留 1–2 帧失败），
  `ok` 路径未证。
- 无 ESD timer；静默卡低只能重启。
- 证据：G1–G6；首次 10 min `isr 2381→6004`、`ok=5997`、`fail=7`；约
  5 min 压测 `isr 8672→13282`、`ok=12866`、`fail +9`；无 panic/STUCK/
  重激活。G7（0177 回退）和 G8（USB re-plug）按决定取消。

## 7. Bring-up 记录（含错误路径）

| 阶段 | 目标 | 结果/结论 |
|---|---|---|
| P0 | 只读寄存器 | LK 留 IOVDD pin110 DO=0；SPI3 未配置；CG 已开 |
| P1/P1b | 控制器 PIO | 误把 SET 当开钟，实际关钟；全 0 是预期 |
| P1c | CLR 开钟、mode 2 | SPI3 寄存器工作，但 Goodix 全 0 |
| P1d | IOVDD 拉高 | 仍全 0；VMC 未确认 |
| P1e | I2C5 普通读写 | LDO 读到 `0x80`，写不进；协议错 |
| P1f | CRC8 block | LDO3/LDO2 0x80→0xC4，仍全 0 |
| P1g | GPIO bit-bang SPI | 链路验证（CS→DI 自检通过），芯片仍沉默 |
| 关键发现 | Android dmesg 电压 | 默认 VMC 3.0 V / VTP 1.8 V，probe 没写 VOUT |
| P1h | 显式写 VOUT | 蓝屏：LLVM SLP 生成 `ldur s0,[x0,#2]`，MMU 关时 alignment fault |
| P1h2 | 关向量化 + volatile | **BERLIN/9916R、CONF/VER 全通过** |
| P2 | 30 s 帧轮询 | 真实触摸帧、checksum、raw x/y 全部有效 |
| P3 | XNU 驱动 | 真实底边上滑解锁、双指 contact 分发、edge |

额外教训：

- `VER CS ok=1` 对全 0 也是真，必须额外拒绝全零数据；
- probe 运行在 MMU 关闭的 Device 语义下，编译器可能生成非对齐宽访问；
  `-mstrict-align` 不够，还要 `-fno-vectorize -fno-slp-vectorize`；
- TWRP 的 adb 读日志用 `dd` + `adb pull`（旧 adb 没有 `exec-out`）；
  Git Bash 要设 `MSYS_NO_PATHCONV=1`，否则 `/tmp` 会被改写成 Windows 路径。

## 8. 调试清单

1. I2C5 空闲时 SCL/SDA 都为 1；否则先查 pinmux/输入使能。
2. 读 LDO3/LDO2 EN/VOUT；旧值通常是 `0x80/0xB0`、`0x80/0x40`。
3. 写 VOUT 后回读必须是 `0x3A/0xD0`；EN 使能后应为 `0xC4`。
4. `dev_confirm` 失败：先看复位时序、IOVDD、SPI 线序。
5. 版本失败：看 ROM 是否 `BERLIN`、checksum 与 sensor。
6. 帧一直全 0：确认 CS/CLK/MISO 和 sync 清零；若用控制器，先修 FIFO。
7. 有帧但无触摸：检查 `event & 0x80`、`touch_num`、point checksum、
   `raw/10` 和 HID 侧 `touch()`。
8. 坐标方向：Android Touch Mapper 显示 `YScale=0.100`、无翻转，所以
   `raw/10` 直接使用；若实机上下颠倒，在驱动里做 `y = 2399 - y/10`。

## 9. 复现、CI 与刷机

- 补丁：`patches/0085-ruby-goodix-spi.patch`；
- canonical patchset：`cf4008e3…c0a03f`（88 文件，和构建出实机内核的
  harness patchset 完全一致）；
- 构建：`.github/workflows/xnu.yml` 拉固定 baseline、应用 delta、跑
  `ci/prepare-baseline.sh`，再用 `ci/kernel_hash.py` 校验内核分段；
- 实机内核：`9eb9acac…`；exec-data `e4823afb…`；boot 镜像 `ace60d16…`；
- cmdline：`config/0085-boot.cmdline`（`sweetgt=1`，无 autoswipe）；
- 刷机：只写 `boot_a`；回滚镜像和 Magisk 基底保持在仓库外。安全边界见
  `docs/records/SAFETY.md`：不写 preloader/lk/persist/nvram，不碰 UFS GPT。

## 10. 证据

实机 sweetlog 的脱敏摘录：

```
SWEET GT: LDO3 en=80 vout=b0, LDO2 en=80 vout=40
SWEET GT: rails on en3=c4 en2=c4
SWEET GT: BERLIN/9916R ready, 1080x2400
```

触摸统计：413 条 `SWEET HID: touch`，206 down / 206 up，40 条 finger-1
（不是 40 帧双指），84 条 edge；down x 0–1038、y 5–2399；无
stopped/panic/fail。两指同时按下时 `SweetHIDTouch::touch()` 会把两个
finger 都 append 到同一个 digitizer collection；用户态 pinch 未单独加日志
验证。完整日志在仓库外，只保留上述摘录和统计。
