# 触控合同

2026-10-22 在作者设备上用 Android 12 / MIUI 13.0.4 的 `su` 只读取证。
原始日志仅保留在本地私有归档（gitignore，不提交、不分享；可能含设备标识；
dmesg、getevent、input-devices、interrupts、vendor-firmware、getprop、
live FDT）；本文件只放脱敏结论。

状态：`confirmed` = 有运行时日志/DT/FDT 证据；`inferred` = 从证据推导，
还需源码或 probe 验证；`unknown` = 还没拿到。

## 1. 身份与软件

| 字段 | 值 | 证据 | 状态 |
|---|---|---|---|
| 设备 | Redmi Note 12 Pro 5G，`ruby` / MT6877，model `22101316C` | `getprop` / `adb devices` | confirmed |
| ROM | MIUI 13.0.4.0.SMOCNXM，Android 12，build `SP1A.210812.016` | `getprop` | confirmed |
| 内核 | `4.19.191-gb349e755cee0` | `uname -a` | confirmed |
| 面板 | `m16_36_02_0b` | `/proc/cmdline` | confirmed |
| 面板/触控变体 | **TM**（`TP is goodix, panel is TM`） | dmesg 2.269033 | confirmed |
| 触控 IC | Goodix GT9916R，BerlinD，PID `9916R`，ROM PID `BERLIN` | dmesg 2.269185、2.425949 | confirmed |
| 芯片 VID / sensor | `00 80 02 64` / `sensor_id 255` | dmesg 2.425951 | confirmed |
| 驱动 | `gtx8_spi`，Goodix core `v1.2.2` | dmesg 2.269038、2.269220 | confirmed |
| 驱动形态 | **内建**：`CONFIG_TOUCHSCREEN_GOODIX_BRL_9916=y`；无 `gtx8_spi.ko` | `/proc/config.gz`、`/proc/modules`、`/vendor/lib/modules` | confirmed |
| 驱动调试节点 | `/sys/devices/platform/goodix_ts.0/`：`chip_info`、`driver_info`、`irq_info`、`esd_info`、`report_rate`、`read_cfg`、`reg_rw`、`get_rawdata` | sysfs | confirmed |
| 报告率 | **240HZ** | `goodix_ts_report_rate` | confirmed |
| 调试节点风险 | `cat fwupdate/goodix_sysfs_fwsize` 触发 `CFI failure (target: goodix_sysfs_fwsize_show)`，内核 BUG/重启；`fwupdate` 是 plain kobject + `DEVICE_ATTR`，CFI 签名不匹配。不要读 `fwupdate/*`，不要写 `reg_rw`/`reset`/`send_cfg` | pstore `console-ramoops-0`；`goodix_brl_fwupdate.c:1165-1180` | confirmed |
| vendor 驱动源码路径/commit |  | `ruby-s-oss` 待查 | unknown |

## 2. 总线、引脚、电源

| 字段 | 值 | 证据 | 状态 |
|---|---|---|---|
| SPI 控制器 | SPI3 `0x11013000`，大小 `0x100` | DT `spi3@11013000/reg` | confirmed |
| SPI compatible | `mediatek,mt6765-spi` | DT | confirmed |
| SPI 控制器 IRQ | `<0 206 4>` → GIC SPI 206 / hwirq 238 | DT；`/proc/interrupts` `GICv3 238 Level 11013000.spi3` | confirmed |
| SPI CS | `reg=<0>` → CS0 | DT `m16-touch@0/reg` | confirmed |
| SPI max speed | `0x4c4b40` = **5,000,000 Hz** | DT `spi-max-frequency` | confirmed |
| SPI mode | mode 0（无 `spi-cpol` / `spi-cpha` / `spi-cs-high`） | DT 属性缺失 | inferred |
| SPI 位宽 | 8-bit（无 tx/rx bus-width 属性） | DT 属性缺失 | inferred |
| SPI pad-select | `0` | DT `mediatek,pad-select` | confirmed |
| 触控 IRQ GPIO | **pin 14**；Linux 全局 44 | DT `goodix,irq-gpio = <&pio 14 ...>`；dmesg `irq-gpio[44]` | confirmed |
| IRQ 类型 | EINT 14，**edge falling**；Linux IRQ 215 | DT `interrupts=<14 ...>`、`goodix,irq-flags=2`；`/proc/interrupts` `mt-eint 14 Edge goodix_ts` | confirmed |
| reset GPIO | **pin 15**；Linux 全局 45 | DT `goodix,reset-gpio = <&pio 15 0>`；dmesg `reset-gpio[45]` | confirmed |
| reset 极性/延时 |  | vendor 驱动待查 | unknown |
| IOVDD 开关 | **pin 110**；Linux 全局 140；高=开，低=关 | DT `goodix,iovdd-gpio`；pinctrl `ts_dvddenable` output-high / `ts_dvdddisable` output-low；dmesg `iovdd-gpio[140]` | confirmed |
| AVDD | MT6360 LDO2，name `vtp`，**3.3 V**，`regulator-default-on` | FDT `/i2c5@11d00000/mt6360_ldo_dts/ldo2`；sysfs `regulator.60` | confirmed |
| IOVDD | MT6360 LDO3，name `VMC`，**1.8 V**，当前 enabled、`num_users=1` | FDT `ldo3`；sysfs `regulator.61` | confirmed |
| IOVDD 是否默认开 | FDT 没有 `regulator-default-on`；Android 由触控驱动 enable | FDT / regulator sysfs | open |
| LK 退出时 SPI3/pins/电源状态 |  | 需要 probe 读寄存器 | unknown |
| 时钟 | `clock-names = parent-clk, sel-clk, spi-clk`；3 个 clock 句柄 | DT `spi3@11013000/clock-names`、`clocks` | confirmed |
| SPI clock 频率/门控寄存器 |  | vendor 源码/probe 待查 | unknown |
| debugfs 汇总表 | **不可用**：`CONFIG_DEBUG_FS is not set`，`/d` 悬空；`clk_summary`/`regulator_summary`/`pinctrl` 都不存在 | `/proc/config.gz`、挂载测试 | confirmed |
| tracefs 替代 | `spi`/`clk`/`regulator`/`gpio`/`irq` 事件存在；`spi` 只有 bus/cs/len，没有 payload | `/sys/kernel/tracing/events` | confirmed |

### 平台物理基址（live FDT，不是 stock DTB）

| 节点 | 物理基址 | 来源 |
|---|---|---|
| SPI3 | `0x11013000` + `0x100` | `/spi3@11013000/reg` |
| pinctrl GPIO | `0x10005000` | phandle `0x3a` → `/gpio@10005000` |
| EINT | `0x1000b000` | phandle `0x43` → `/eint@1000b000` |
| IOCFG banks | `0x11c20000`、`0x11c30000`、`0x11d10000`、`0x11d30000`、`0x11d40000`、`0x11e20000`、`0x11ea0000`、`0x11f30000` | `/pinctrl` 的 `reg_bases` phandles |
| topckgen | `0x10000000` + `0x1000` | phandle `0x47` → `/syscon@10000000` |
| infracfg_ao | `0x10001000` + `0x1000` | phandle `0x45` → `/syscon@10001000` |
| SPI3 clocks | `parent-clk 0x9`、`sel-clk 0x90`、`spi-clk 0x2a` | DT `clocks` |
| I2C5 / MT6360 | `0x11d00000` / `0x64` | DT `i2c5@11d00000`、`5-0064` |
| MT6360 LDO2 / LDO3 | `vtp` 3.3 V / `VMC` 1.8 V | DT `mt6360_ldo_dts/ldo2`、`ldo3` |
| i2c-tools | 二进制存在，但 **无 `/dev/i2c-*`**；`CONFIG_I2C_CHARDEV is not set` | `/proc/config.gz`、`/dev` | confirmed |
| SPI 寄存器块 | `CFG0 0x00`、`CFG1 0x04`、`TX_SRC 0x08`、`RX_DST 0x0c`、`TX_DATA 0x10`、`RX_DATA 0x14`、`CMD 0x18`、`STATUS0 0x1c`、`STATUS1 0x20`、`PAD_SEL 0x24`、`CFG2 0x28` | `spi-mt65xx.c` | confirmed |
| mt6765 quirks | `need_pad_sel`、`must_tx`、`enhance_timing`、`dma_ext` | `spi-mt65xx.c:127-132` | confirmed |
| FIFO / DMA | FIFO 32 B；34 B 预读 >32，vendor 走 DMA；PIO 需 32+2 保持 CS 分块 | `spi-mt65xx.c:89,660-662,680-740` | confirmed |

**边界：** FDT 给的是控制器 base、bank base、clock ID 和 pin/function
（SPI pins **160-163** function 2；`0xa002` 的高字节 0xA0=160）。它**不提供**：
- clock gate 的具体寄存器/bit（在 `clk-mt6877` 驱动表里）；
- 每个 pin 的 IOCFG 寄存器 offset（在 `pinctrl-mt6877` / common 驱动里）；
- MT6360 LDO2/LDO3 的 enable 寄存器/bit（在 MT6360 regulator 驱动里）。

这三项要么继续拉平台驱动源码，要么由 bare-metal probe 直接读寄存器确认。

### 平台寄存器（`ruby-s-oss@914ba84`）

| 功能 | 寄存器 | 值/说明 |
|---|---|---|
| SPI3 pinmux | `0x10005440` bits [15:0] | `0x2222`：pins 160-163 = function 2 |
| pin14/15 mode | `0x10005310` bits [31:24] | `0`：GPIO function |
| pin110 mode | `0x100053d0` bits [27:24] | `0`：GPIO function |
| reset 15 | DIR `0x10005000` bit15=1；DO `0x10005100` bit15 | 低/高由 DO 控制 |
| IRQ 14 | DIR `0x10005000` bit14=0；DI `0x10005200` bit14 | 输入 |
| IOVDD 110 | DIR `0x10005030` bit14=1；DO `0x10005130` bit14=1 | 输出高=开 |
| SPI3 gate | **CLR `0x100010a8` bit10=1 开钟**；SET `0x100010a4` bit10=1 关钟；STA `0x100010ac` bit10=1 表示 gated，0 表示 ungated | `CLK_IFRAO_SPI3`，IFRAO2；`clk-gate.c:135-167,225-235` |
| SPI3 mux | `0x10000070` bits [9:8]（set `0x74`/clr `0x78`），update `0x10000004` bit25 | 1 = `mainpll_d5_d4`（DTS parent ID 9） |
| LDO3 VMC | I2C5 `0x64`，reg `0x05` bit6（mask 0x40） | enable；8-bit regmap |
| LDO2 vtp | I2C5 `0x64`，reg `0x11` bit6（mask 0x40） | default-on；3.3V |

pinctrl 的 mode/dir/do 字段来自 `pinctrl-mt6877.c` 的 range 表；IOCFG 的
drive-strength/bias 未列入，第一版 PIO 可以先不做。SPI3 mux 的父时钟
实际频率还没测；probe 先读 `CLK_CFG_6`/gate 状态，再用保守 divider。

**P0 live（2026-10-22）：** SPI3 CFG0/CFG1=0、CMD/ST0=0、PAD/CFG2=0；
TOP `CLK_CFG_6=0x01010100`（mux=1）；IFRAO set/sta=0；PINMUX
`0x10005440=0x01100000`（低 16 位 0）、`0x10005310=0x00220000`、
`0x100053d0=0x00001111`；GPIO dir0=`0xC0208408`、dir30=`0x0040F000`、
do00=`0x80000600`、do30=`0x00401000`、di00=`0xBC875FA9`。
判读：**IFRAO sta=0 表示 SPI3 clock 已 ungated/开**；LK 留了 top mux=1、
gate 开、reset 高、IRQ 输入；**IOVDD pin 110 的方向是输出，但 DO bit14=0，
即开关是关的**（`do30=0x00401000` 的 0x4000 位为 0）。SPI3 pinmux 和
控制器仍要配置；P0 时 SPI3 寄存器已经全 0，所以除了 pinmux 还另有
控制器不可访问的问题。

**P1/P1b live（2026-10-22，含错误）：** P1/P1b 向 **SET** `0x100010a4`
写 bit10，实际是 **gated/关钟**；`sta=0x400` 也表示 gated。因此
`SPI` 全 0 是预期，**不能**据此判断 mux/电源。P0 时 `sta=0` 本来是开钟。

**P1c live（2026-10-22）：** 写 **CLR** `0x100010a8` bit10 开钟后，
`sta=0`（ungated）；SPI3 `CFG0=003F003F`、`CFG2=001F001F`、
`CMD=00033000`，传输 `st=1`。SPI3 控制器/总线已工作。但 `CONF R`/
`VER` 数据全 0，Goodix 未响应。P1c **没有写 pin 110 的 DO**；P0 的
`do30=0x00401000` bit14=0 说明 IOVDD 开关一直是关的，这是首要嫌疑。
`SPI_CFG0=003F003F` 不是 CPOL/CPHA（Mode 在 `SPI_CMD` bit8/9，
`CMD=00033000` 仍是 Mode 0）。P1d 先把 pin110 拉高；VMC/LDO3 是
第二嫌疑。

**P1d live（2026-10-22）：** `touch-p1d.img`，SHA-256
`e45d4d94…aeb3aaa8`；`IOVDD do30=0x00405000`（开关已开），SPI3 正常，
但 `CONF`/`VER` 仍全 0。IOVDD 开关不是唯一缺口；VMC/CS/MISO 仍待查。
P1d 热重启（Android VMC enabled → 不断电进 fastboot → P1d）结果仍全 0；
LK 可能重关 VMC，负结果仍不决定性。下一步必须直接量 VMC 或 P1e I2C5
读/写 MT6360 LDO3，不要继续热重启。

**P1e live（2026-10-22）：** GPIO bit-bang I2C5 读 ACK 正常，
LDO3/LDO2 都读到 `0x80`、bit6=0，但写 `old|0x40` 回读仍 `0x80`。
源码确认 MT6360 LDO 不是普通寄存器协议，而是 **CRC8 保护的 SMBus
block**；P1e 的单字节读写无效，0x80 不可信。

**P1f live（2026-10-22）：** `touch-p1f.img`，SHA-256
`fe100afea94abf5b4cd15dc57fb517152076d3dbbd1086455de80366d56856c7`。
LDO3 `0x80 → 0xC4` bit6=1；LDO2 `0x80 → 0xC4` bit6=1；CRC8 block
协议有效，**VMC/VTP 已 enable**。IOVDD/SPI3 正常，但 `CONF`/`VER`
仍全 0。

**P1g live（2026-10-22）：** `touch-p1g.img`，SHA-256
`e93b74fcb0b369b7df72d710d83c0a394b0df56c03815455f230bd476137e4e0`。
SPI3 pins 160-163 切 GPIO（160=MO/161=MI/162=CSB/163=CLK），
Mode 0 bit-bang：`DI TEST cslo=0 cshi=1` 证明 bank5 DI 通路有效；
`CONF ok=0`（250 kHz/50 kHz 均失败）、`CONF R`/`VER` 全 0。
bit-bang 链路本身已验证，芯片仍沉默。`VER CS ok=1` 是全 0 假阳性。

**LDO 默认电压（关键）：** Android dmesg 1.395 s 显示
`vtp: Bringing 1800000uV into 3300000-3300000uV`、
`VMC: Bringing 3000000uV into 1800000-1800000uV`。即 LK/PMIC 默认
**LDO3 VMC=3.0 V、LDO2 vtp=1.8 V**，Android 启动后才改成
1.8 V/3.3 V。P1f/P1g 只写 enable 位、没写 VOUT（LDO3 `0x09`、
LDO2 `0x15`），所以触控实际拿到 IOVDD 3.0 V、AVDD 1.8 V，
AVDD 欠压，芯片不会启动。P1g 读到的 `old=0x80`（enable=0）
说明 PMIC 在进入 probe 前已复位到默认，warm reboot 同样无效。

**P1h（已刷入并运行，随后 panic）：** `touch-p1h.img`，SHA-256
`b4663587882cb225619985bcf2257fd780b24daad1c519ea1af5762fffc93a9b`。
读 LDO3/LDO2 EN+VOUT（CRC8）→ 断电 20 ms → VMC `0x09=0x3a`
（1.8 V）、vtp `0x15=0xd0`（3.3 V）→ 回读 → IOVDD 高 →
使能 LDO3/30 ms → 使能 LDO2/15 ms → 复位 → bit-bang
`dev_confirm`/版本/26 字节帧预读。

**P1h live panic：** 打印到 `CONF` 后在 `ver_ok` 蓝屏，
`ESR=0x96000021` alignment fault、`FAR=0x4008C792`。原因是 LLVM
SLP 向量化把 `ver_ok` 的字节和生成 `ldur s0,[x0,#2]`（`rx+10`
4 字节非对齐 load）；probe 关 MMU，Device 语义下直接 fault。
**P1h2**（`touch-p1h2.img`，SHA-256
`582fd761c8f6867b7ccb781c650aada8d433dff3cfeb6ee0e32669d36a8cae8e`）
在 build.sh 关闭 `-fno-vectorize/-fno-slp-vectorize`，并把字节缓冲
读取改成 volatile；反汇编已确认无非对齐宽访问。逻辑与 P1h 相同。

**P1h2 live（2026-10-22，成功）：** `LDO3 vout 0xB0(3.0 V)→0x3A(1.8 V)`、
`LDO2 vout 0x40(1.8 V)→0xD0(3.3 V)` 后，`CONF ok=1`（250 kHz）、
`CONF R=AAAAAAAA`、`VER CS ok=1`、`ROM=BERLIN`、`PID=9916R`、
`sensor_id=0xFF`、`patch_vid=00 80 02 64`；`FRAME head_ok=1`,
`event=0x80`（`GOODIX_TOUCH_EVENT`）, `touch_num=0`。芯片/SPI/
复位/固件全部正常，**根因就是 probe 未写 LDO VOUT**。

**P2（已构建并运行，通过）：** `touch-p2.img`，SHA-256
`3d18d7a7bd1a8b1541d8233a276c60ba3635dc830ff90532636d6ed2d3c086ec`。
P1h2 上电序列 + 30 秒轮询 `0x10308` 34 字节，校验 head/point、
清 sync、输出 raw x/y/w 和统计。live：`TCH n=1` 的 point checksum
全部有效，raw x≈2612–9493、y≈12012–20260（10800×24000 内），
轮询约 80–100 Hz。Android Touch Mapper `YScale=0.100` 无翻转，
P3 默认 `raw/10`。

**热重启验证：** Android 中 `VMC=enabled 1.8V`，`adb reboot bootloader`
后刷 P1c，结果仍全 0；PMIC 复位后 VOUT/enable 回默认，负结果不能
证明 VMC 无关。

## P3 — XNU 集成

补丁：`work/ios-ruby/xnu/patches/0085-ruby-goodix-spi.patch`
（本地 commit `8716a06`，未推送）。改动：

- 新文件 `bsd/dev/sweet_goodix_spi.c`：XNU 内核线程 + `ml_io_map`，
  复用已验证的 I2C5 bit-bang + MT6360 CRC8 LDO3/LDO2
  （`0x09=0x3a`、`0x15=0xd0`）、IOVDD pin110、复位 pin15、
  SPI3 pins 160-163 Mode 0 bit-bang；轮询 `0x10308` 34 字节，
  head/point checksum 通过后调用 `sweet_hid_touch(id, 1, raw/10, raw/10)`；
- `bsd/conf/files` 一行；`bsd/dev/sweet_ufs.c` 增加 extern 和
  `sweet_goodix_spi_init()` 调用（`sweetgt=0` 可关闭）；
- 第一版（0085）限制：≤2 指、无 IRQ/ESD/固件下载；PMIC 只写 LDO3/LDO2
  EN+VOUT，不动 UFS/显示/其他 PMIC 位。0179 已改用 EINT14 oneshot
  （1–5 指帧），ESD timer 与固件下载仍未实现。

本地校验：`git apply --check` 通过；用桩内核头文件做
`clang -fsyntax-only` 通过。CI 构建用固定 harness 仓库的 `ruby` 分支，
push `xnu/patches/**` 触发，artifact 名 `xnu-kernel`。

**P3 live（2026-10-22，成功）：** CI run `39688537951`，
kernel SHA-256 `9eb9acac8a4c936c1861fba1e0d29c105b714e8d0e6d407b48f4237076e6b947`；
boot 镜像 `<workdir>/root/boot_a_ruby_ios_cpus6_wifi_stub_0085_gt_full.img`，
SHA-256 `ace60d1645ec271cdbd55b7007456cb578168ca708382aafae8fbf506e68f6c8`。
刷入后 sweetlog 显示：

```
SWEET GT: LDO3 en=80 vout=b0, LDO2 en=80 vout=40
SWEET GT: rails on en3=c4 en2=c4
SWEET GT: BERLIN/9916R ready, 1080x2400
```

`SWEET HID: touch` 共 413 行：206 down / 206 up、40 条 finger-1（touch 1）、
84 条 edge；down 坐标 x 0–1038、y 5–2399；无 `stopped`/panic/fail。
真实触摸、锁屏底边上滑工作，**不需要 Y 翻转**；两指同时按下时
`SweetHIDTouch` 会把两个 finger 拼进一个 collection，但用户态 pinch 未
单独加日志验证。
原始日志：本地私有归档（raw 原件与日志均不入库）。

### pinctrl（FDT 解析）

| 状态 | pin | function | 其他 |
|---|---|---|---|
| `ts_spimode` | 160, 161, 162, 163 | 2（SPI） | drive-strength 2 |
| `ts_reset_active` | 15 | 0（GPIO） | bias-disable |
| `ts_reset_suspend` | 15 | 0（GPIO） | slew-rate 1，bias-pull-down |
| `ts_int_active` | 14 | 0（GPIO） | bias-disable |
| `ts_int_suspend` | 14 | 0（GPIO） | slew-rate 1，bias-disable |
| `ts_dvddenable` | 110 | 0（GPIO） | output-high |
| `ts_dvdddisable` | 110 | 0（GPIO） | output-low |

pinmux 原始值：`ts_spimode = 0xa002/0xa102/0xa202/0xa302`；
`ts_reset_active = 0xf00`；`ts_int_active = 0xe00`；
`ts_dvddenable = 0x6e00`。

> DT 用 pin 号；Linux 驱动日志里的 44/45/140 是 pin + 30 的全局 GPIO 号。
> 30 是运行时 gpiochip base，不是 DT 值。

## 3. 固件

| 字段 | 值 | 证据 | 状态 |
|---|---|---|---|
| 固件文件名 | `goodix_firmware_m16_TM.bin` | dmesg 2.269534；ueventd 日志 | confirmed |
| 配置文件名 | `goodix_cfg_group_m16_TM.bin` | dmesg 2.269536 | confirmed |
| 变体 | **TM** | dmesg 2.269033 | confirmed |
| 固件大小 / SHA-256 | 223,744 B / `4a3baefe...379424d7` | `/vendor/firmware` | confirmed |
| 配置大小 / SHA-256 | 1,421 B / `8974708b...750121db` | `/vendor/firmware` | confirmed |
| GVO 文件 | 同样存在；本次未使用 | `/vendor/firmware` | confirmed |
| 固件包协议 | V0 | dmesg 5.601581 | confirmed |
| 固件 PID/VID | `GT9916R` / `00 80 02 64` | dmesg 5.601584 | confirmed |
| 固件 chip type | `0x98` | dmesg 5.601588 | confirmed |
| 固件包内 bus type | `I2C`（只是包元数据，不是实际总线） | dmesg 5.601590 | confirmed |
| 固件包大小 / subsystem | 223,736 B / 6 | dmesg 5.601592 | confirmed |
| 版本比较 | `fw_version equal`、`config_id equal` | dmesg 5.601726、5.601770 | confirmed |
| 本次是否真正烧录 | **没有**；`goodix_fw_update_proc()` 在版本比较返回 0 时直接 `return 0`，不会进入 prepare/flash；日志 `firmware upgraded` 是“无需升级” | `ruby-s-oss@914ba84` `goodix_brl_fwupdate.c:437-488,935-953`；dmesg 5.601773 | confirmed |
| 片内固件状态 | 芯片已有可运行 TM 固件；版本相等时不下载、不重烧 | 同上 | confirmed |
| 每次上电是否必须 host 下载 | **不需要**（版本/config 相等时）；只有版本或 config 不等才走更新路径 | 同上 | confirmed |

**结论：** 芯片已经带着 TM 固件和 config（`0x6333C2A1`）。源码确认
`goodix_fw_update_proc()` 在 `goodix_fw_version_compare()` 返回 0 时直接
返回，不进入 `goodix_update_prepare()`/`goodix_flash_firmware()`。所以最小
XNU 驱动不需要加载 `/vendor/firmware`；版本相等即可直接运行芯片内固件。

## 4. 初始化与上报

源码基准：`ruby-s-oss` 分支 `914ba84`，`drivers/input/touchscreen/goodix_9916r/`。

### 4.1 上电、复位、确认

`brl_power_on()`（`goodix_brl_hw.c:175-213`）对这块板子的实际顺序：

1. IOVDD GPIO pin 110 拉高，`usleep 3 ms`；
2. `regulator_enable(iovdd)` = VMC 1.8 V，`usleep 30 ms`；
3. `regulator_enable(avdd)` = vtp 3.3 V，`usleep 15 ms`；
4. reset pin 15 拉高（GPIO 初始为低），调用 `brl_reset_after()`；
5. `msleep 100 ms`。

`brl_reset_after()` 对 **BerlinD 直接返回 0**：SPI mode 切换、锁 CPU、
group0/1 clock、D12、软复位这一整套只对 BerlinA 执行
（`goodix_brl_hw.c:55-173`）。所以这块芯片没有额外的 soft-reset 命令序列。

热复位 `brl_reset()`：reset 低 2 ms → 高 → 100 ms
（`goodix_brl_hw.c:311-324`）。

`brl_dev_confirm()`：向 `0x10000` 写 8 个 `0xAA`，回读 8 字节比较，
最多 3 次，间隔 5 ms（`goodix_brl_hw.c:280-309`）。

`brl_read_version()`：读 `0x10014` 共 28 字节，U8 LE checksum
（`goodix_brl_hw.c:644-690`）。期望 ROM PID `BERLIN`、patch PID `9916R`、
VID `00 80 02 64`。

### 4.2 SPI 读/写（BerlinD）

`goodix_brl_spi.c:102-190`：

- 读：`0xF1 + addr(4, big-endian) + 0xFF*3` = **8 字节前缀**；
  SPI 总长 = 8 + len；数据从 `rx[8]` 开始。
- 写：`0xF0 + addr(4, big-endian)` = **5 字节前缀**；
  总长 = 5 + len。
- `spi->mode = SPI_MODE_0`，`bits_per_word = 8`（`goodix_brl_spi.c:229-231`）。

### 4.3 触摸上报

`brl_event_handler()` / `goodix_touch_handler()`
（`goodix_brl_hw.c:1010-1259`）：

- 先读 **26 字节**（线上 transfer = 8 + 26 = **34**）：
  - `buf[0]` event_status：`0x80` TOUCH、`0x88` POWERON_FOD、`0x40`
    REQUEST、`0x20` GESTURE、`0x10` LARGE_TOUCH；
  - `buf[2] & 0x0F` = touch_num；`buf[2]` 的同字节高位是 large-touch 状态；
  - `buf[6..7]` = 前 6 字节的 U8 LE checksum；
  - `buf[8..]` 是前两个 8 字节 point + 2 字节 checksum。
- 如果 `touch_num > 2`，再从 `0x10308 + 26` 追加读
  `(touch_num - 2) * 8 + 10` 字节（线上 transfer = 8 + 该长度）：
  - `touch_num=3` → 26；
  - `touch_num=4` → 34；
  - `touch_num=5` → 42。
- 点结构 8 字节（`goodix_parse_finger()`）：
  - `[0]` 高 nibble = finger id，低 nibble = point type（1/3 为 stylus）；
  - `[1]` 普通手指不使用，FOD 时参与；
  - `[2..3]` x LE16；
  - `[4..5]` y LE16；
  - `[6..7]` w LE16。
- 触摸数据 checksum：从 `buf[8]` 开始 `touch_num*8 + 2` 字节，U8 LE
  （`goodix_ts_utils.c:70-93`）。
- 处理完必须向 `0x10308` 写 1 个 `0x00` 清 sync（线上 **6** 字节）；
  否则下一帧/IRQ 可能不更新（`goodix_brl_hw.c:1251-1259`）。
- ESD：每 3 秒读 `0x10170` 1 字节；值不是 `0xAA` 就写 `0xAA`
  （`goodix_brl_hw.c:981-1008`；`goodix_ts_core.c:1913-1960`）。
  线上是 **9 字节读 + 6 字节写**，不是触摸上报。

| 字段 | 值 | 证据 | 状态 |
|---|---|---|---|
| chip ID / version | `0x10014`，28 字节 | `goodix_brl_hw.c:644-690` | confirmed |
| dev confirm | `0x10000`，8×`0xAA`，回读比较 | `goodix_brl_hw.c:280-309` | confirmed |
| 复位/上电 | 见 4.1；BerlinD 无软复位序列 | `goodix_brl_hw.c:175-213` | confirmed |
| 预读包 | 26 字节（8 head + 2 point + 2 checksum） | `goodix_brl_hw.c:1198-1201` | confirmed |
| 追加读 | `touch_num>2`，长度 `(n-2)*8+10` | `goodix_brl_hw.c:1121-1129` | confirmed |
| 单点结构 | 8 字节，x/y/w 在 `+2/+4/+6` | `goodix_brl_hw.c:1023-1055` | confirmed |
| sync 清零 | `0x10308` 写 1 字节 0 | `goodix_brl_hw.c:1251-1259` | confirmed |
| ESD tick | `0x10170` 读 1 / 写 1（0xAA） | `goodix_brl_hw.c:981-1008` | confirmed |
| 中断标志 | `IRQ:215, flags:2`（falling） | dmesg 5.602441 | confirmed |

## 5. 输入映射

| 字段 | 值 | 证据 | 状态 |
|---|---|---|---|
| input 设备名 | `goodix_ts` | `/proc/bus/input/devices` | confirmed |
| event 节点 | `/dev/input/event5` | getevent | confirmed |
| ABS_X / ABS_Y | 0..10800 / 0..24000 | getevent | confirmed |
| ABS_MT_SLOT | 0..9 | getevent | confirmed |
| ABS_MT_TRACKING_ID | 0..65535 | getevent | confirmed |
| ABS_MT_TOUCH_MAJOR | 0..255 | getevent | confirmed |
| ABS_MT_WIDTH_MAJOR | 0..100 | getevent | confirmed |
| 按键 | BTN_TOUCH、BTN_TOOL_FINGER、KEY_POWER、KEY_WAKEUP | input-devices | confirmed |
| input props | `INPUT_PROP_DIRECT` | getevent | confirmed |
| Android 逻辑分辨率 | 1080×2400 | getevent / 面板 | confirmed |
| iOS 逻辑分辨率 | 1125×2436，偏移 22/18 | [04-display](../docs/zh/04-display.md#L3) | confirmed |
| 现有 `touch()` 坐标约定 | **面板像素 0..1079 × 0..2399**；内部再映射到 1125×2436（offsets 22/18） | `SweetHID.cpp` 570-577 | confirmed |

### 2026-10-22 输入抓取

60 秒窗口，实际有触摸事件 36.3 秒；4,783 条事件，1,175 个
`SYN_REPORT`。

| 观察 | 结果 |
|---|---|
| 活跃报告间隔 | 中位数 **4.2 ms**（约 238 Hz），最短 1.6 ms |
| 平均报告率 | 32.4 Hz（被手势间长空闲拉低） |
| 触摸会话 | 56 次；最大并发 2 指 |
| 多点 slot | `ABS_MT_SLOT` 出现 0 和 1 |
| 四角 | 左上 `(837,753)`、右上 `(9759,766)`、左下 `(1012,23515)`、右下 `(8976,23925)` |
| 方向 | x 向右、y 向下；与面板坐标一致 |
| 压力/宽度 | `ABS_MT_TOUCH_MAJOR` / `ABS_MT_WIDTH_MAJOR` 声明了但**没有事件** |
| IRQ | EINT14 的 8 核计数从合计 196 到 2,085，增量 **1,889** |
| dmesg | 没有 Goodix 错误；只有无关的 MTK DBGTOP timeout |

**判断：** Linux input 输出层健康，坐标方向正确，双指 slot 可用，EINT14
确实在跑；但驱动不报压力/宽度，XNU 侧只需要位置、tracking 和 slot。
`getevent` 只能看到 Linux input 层，看不到 SPI 原始包/寄存器/校验。

**对 probe 的影响：** 活跃期约 240 Hz；第一版 100–125 Hz 轮询能做出可用
触摸，但会丢一部分样本。要还原完整手感，第二版用 EINT14 或把轮询提到
250 Hz。HID 层已有 50 ms 步进的合成滑动，100 Hz 足够证明链路，不是最终
采样率。

### 2026-10-22 SPI 长度抓取（tracefs）

60 秒 trace，181,834 条事件；SPI3 共 9,529 个 message，其中 IRQ 线程
`irq/215-goodix_` 发起 7,014 个。**没有 tx/rx payload，只有 bus/cs/len。**

| transfer 长度 | 总数 | IRQ 线程 |
|---|---:|---:|
| 34 | 4,659 | 3,476 |
| 6 | 4,547 | 3,409 |
| 42 | 163 | 51 |
| 26 | 155 | 78 |
| 9 | 5 | 0 |

IRQ 线程的主导序列是 **34 → 6**，下一轮再从 6 → 34；活跃期约每 4 ms
一轮（和 getevent 的 4.2 ms 中位间隔一致）。少量变体：

- `34 → 26 → 6`：78 次；
- `34 → 42 → 6`：51 次；
- `34 → 34`：66 次。

源码解释（`goodix_brl_hw.c:1121-1129`）：26/42 **不是另一套协议**，而是
`touch_num > 2` 时在预读之后追加读：

- 预读固定 26 字节 → 线上 34；
- `touch_num=3` 追加 18 字节 → 线上 26；
- `touch_num=4` 追加 26 字节 → 线上 34（所以出现 `34→34`）；
- `touch_num=5` 追加 34 字节 → 线上 42。

6 字节是 `brl_after_event_handler()` 向 `0x10308` 写 1 字节 0 清 sync
（`goodix_brl_hw.c:1251-1259`），不是读命令。

`kworker/7:2-events` 每 ~3.07 秒的 9→6 是
`brl_esd_check()`：读 `0x10170` 1 字节，若不是 `0xAA` 就写 `0xAA`
（`goodix_brl_hw.c:981-1008`；`goodix_ts_core.c:1942` 每 3 秒调度）。
不是触摸上报，基础触摸可以先不做 ESD tick。

**结论：** 主路径已经完整闭合：34 字节预读 → （`touch_num>2` 时）追加读
→ 解析 8 字节 point → 6 字节 sync 清零。协议层不需要再猜。

## 6. 证据索引

| 证据 | 关键内容 |
|---|---|
| dmesg 2.269033 | `TP is goodix, panel is TM` |
| dmesg 2.269185 | `ic type is BerlinD` |
| dmesg 2.269534 | `firmware name ... goodix_firmware_m16_TM.bin` |
| dmesg 2.425949 | `pid:9916R`，VID、sensor id |
| dmesg 5.601726 | `fw_version equal` |
| dmesg 5.601770 | `config_id equal` |
| dmesg 5.602317..5.602343 | Cmd/FW/Touch-Data 地址、point 长度、面板量程 |
| dmesg 5.602441 | `IRQ:215,flags:2` |
| DT `spi3@11013000` | `mediatek,mt6765-spi`、5 MHz、CS0、IRQ 206、clocks |
| DT `pinctrl/ts_*` | SPI pins 160-163、reset 15、IRQ 14、IOVDD 110 |
| FDT `mt6360_ldo_dts/ldo2` | `vtp` 3.3 V，default-on |
| FDT `mt6360_ldo_dts/ldo3` | `VMC` 1.8 V |
| `/proc/interrupts` | `GICv3 238 Level 11013000.spi3`；`mt-eint 14 Edge goodix_ts` |
| `ruby-s-oss@914ba84` | `drivers/input/touchscreen/goodix_9916r/`：SPI 前缀、26/34/42、checksum、上电/复位、fw update、fwsize CFI |

原始日志不提交：仅保留在本地（gitignore；可能含设备标识，不分享）。
固件 blob、设备 dump、序列号/IMEI 不进入本仓库。

## 7. 给 XNU 最小驱动的最小输入

1. **SPI3**：base `0x11013000`，5 MHz，mode 0，CS0，8-bit；先 PIO，无 DMA。
2. **时钟**：`parent-clk / sel-clk / spi-clk` 三个 clock；需要 vendor 的
   门控/频率寄存器映射，或 probe 读 LK 留下的状态。
3. **pinctrl**：SPI 用 pins **160-163** function 2；reset 15、IRQ 14、
   IOVDD 110 为 GPIO function 0。
4. **上电顺序**：pin 110 拉高 → 3 ms → enable VMC 1.8 V → 30 ms →
   enable vtp 3.3 V（default-on）→ 15 ms → reset 15 高 → 100 ms。
   VMC = I2C5 `0x64` reg `0x05` bit6；如果 LK 已把它留在 enable，可跳过。
   然后 `dev_confirm`：向 `0x10000` 写 8×`0xAA`，回读比较；可选读
   `0x10014` 28 B 版本并做 U8 LE checksum。
5. **复位**：BerlinD **没有** SPI mode 切换/锁 CPU/软复位序列
   （`brl_reset_after()` 直接返回 0）；热复位是 reset 低 2 ms → 高 → 100 ms。
   pinctrl 先选 `pmx_ts_active` 和 `pmx_ts_spi_mode`。
6. **上报**：读 `0x10308` **26 B**（线上 34）→ 校验 head →
   `touch_num>2` 时从 `0x10308+26` 追加读 → 解析 8 B point →
   校验 → 向 `0x10308` 写 1 B 0 清 sync（线上 6）。ESD tick 可选。
7. **坐标**：raw 0..10800/0..24000 除以 10 得到面板
   0..1079×0..2399，直接调 `SweetHIDTouch::touch()`；它内部再映射到
   1125×2436（22/18 偏移）。不要把 iOS 逻辑坐标直接喂进去。
8. **IRQ**：第一版 100–125 Hz 轮询，不用 EINT；EINT14 edge falling 留给
   第二版。抓包显示活跃期约 240 Hz，100 Hz 会丢样本但足够先证明链路。

## 8. Open questions

- [x] vendor 驱动源码：`ruby-s-oss@914ba84`，
      `drivers/input/touchscreen/goodix_9916r/`。
- [x] 每次上电是否必须 host 下载固件：不需要；版本/config 相等时
      `goodix_fw_update_proc()` 直接返回，不进入 flash。
- [x] reset 极性/延时/初始化：见 4.1；BerlinD 无软复位序列。
- [x] SPI mode 0 / 8-bit：源码显式设置 `SPI_MODE_0`、8 bit。
- [x] SPI3 clock gate/mux 寄存器：**CLR `0x100010a8` bit10=1 开钟**
      （SET `0xa4`=关钟；STA=1 表示 gated）；mux `0x10000070` bits [9:8]，
      update `0x10000004` bit25。
- [ ] SPI3 mux 父时钟实际频率/divider，以及 LK 退出时 gate/mux 是否已开。
- [ ] IOVDD `VMC` 在 XNU 启动时是否仍 enabled；如果关了，需要 I2C5
      写 MT6360 `0x64` reg `0x05` bit6（XNU 还要 I2C5 控制器驱动）。
- [x] 上报包格式/校验/point 偏移：见 4.3。
- [ ] ESD tick（每 3 秒写 0xAA）是否必须；第一版可以不做，长跑再验证。
- [ ] `dev_confirm` 失败时芯片是否仍能上报；vendor 驱动忽略失败，
      probe 应记录回读值。
