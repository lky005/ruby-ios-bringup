# 附录 — 启动参数与镜像打包参数

**中文** · [English](../en/appendix-bootargs.md)

> 状态标注沿用[仓库 README](../../README.zh.md)。下表默认值取自 0334
> 源码（`ruby_usb_probe()` 等）；基线 cmdline 587 B，上限 607 B。

## 推荐 cmdline 预设（可直接复制）

下面三条都是完整的 `--cmdline` 值，来自已验证的 0332i/0334 构建；内核
默认值未改。

**1）默认路径（587 B，`rubywinusb=4`，hotplug 关）：**

```text
debug=0xc serial=3 cpus=6 keepsyms=1 -noprogress rd=ufsroot0 ufsroot=iosroot ufsrw=1 rootrw=1 sweethw=0 ufslun=2 launchd_unsecure_cache=1 unentitled_ios_sim_launch=1 ignition_level=1 wdt=-1 wdt_test=no_user_checkin sweetfb_noconsole=1 sweetfb_hz=30 rubyusb=1 ufslogsecs=1 rubyprobe=1 rubyep2log=0 rubypwrap=1 rubkeys=1 rubybatt=1 rubyeint=1 rubymt6360=1 rubyeintirq=1 rubykpdirq=1 rubyeintb1=1 rubyusbirq=1 rubyqmuirq=1 rubypad=1 rubydmauc=1 rubyusbcmd=1 ruby_rxskip=1 ruby_txreset=0 ruby_clr01=1 rubyreboot=1 ruby_zlp=0 ruby_enum=0 ruby_echo=1 ruby_iddump=1 rubywinusb=4 rubysetupdump=1
```

**2）开箱即用推荐（605 B）：在上面基础上加 `rubyusb_hotplug=1`，
WinUSB 绑定与端口事件同时开启：**

```text
debug=0xc serial=3 cpus=6 keepsyms=1 -noprogress rd=ufsroot0 ufsroot=iosroot ufsrw=1 rootrw=1 sweethw=0 ufslun=2 launchd_unsecure_cache=1 unentitled_ios_sim_launch=1 ignition_level=1 wdt=-1 wdt_test=no_user_checkin sweetfb_noconsole=1 sweetfb_hz=30 rubyusb=1 ufslogsecs=1 rubyprobe=1 rubyep2log=0 rubypwrap=1 rubkeys=1 rubybatt=1 rubyeint=1 rubymt6360=1 rubyeintirq=1 rubykpdirq=1 rubyeintb1=1 rubyusbirq=1 rubyqmuirq=1 rubypad=1 rubydmauc=1 rubyusbcmd=1 ruby_rxskip=1 ruby_txreset=0 ruby_clr01=1 rubyreboot=1 ruby_zlp=0 ruby_enum=0 ruby_echo=1 ruby_iddump=1 rubywinusb=4 rubysetupdump=1 rubyusb_hotplug=1
```

**3）测试通道 lite 镜像（585 B）：默认集合去掉 `ruby_iddump=1`、加
`rubyep_test=1`；0331 矩阵与 0334 T2 批量都用它：**

```text
debug=0xc serial=3 cpus=6 keepsyms=1 -noprogress rd=ufsroot0 ufsroot=iosroot ufsrw=1 rootrw=1 sweethw=0 ufslun=2 launchd_unsecure_cache=1 unentitled_ios_sim_launch=1 ignition_level=1 wdt=-1 wdt_test=no_user_checkin sweetfb_noconsole=1 sweetfb_hz=30 rubyusb=1 ufslogsecs=1 rubyprobe=1 rubyep2log=0 rubypwrap=1 rubkeys=1 rubybatt=1 rubyeint=1 rubymt6360=1 rubyeintirq=1 rubykpdirq=1 rubyeintb1=1 rubyusbirq=1 rubyqmuirq=1 rubypad=1 rubydmauc=1 rubyusbcmd=1 ruby_rxskip=1 ruby_txreset=0 ruby_clr01=1 rubyreboot=1 ruby_zlp=0 ruby_enum=0 ruby_echo=1 ruby_iddump=1 rubywinusb=4 rubyep_test=1
```

说明：

- `rubyusb_susp=1` 再加 17 B；预设 2 加上它会到 622 B，超过 607 B 上限，
  需要时请删掉一个探针参数。
- 预设 2 开启端口事件；0334 的默认 A/B 证据是 hotplug 关。hotplug 开
  的验证属于 0333 线（10/10 重枚举）。
- `rubywinusb=4` 是 MS OS 1.0 WCID，并把 bcdDevice 提到 `0x0212` 让
  Windows 重新探测 `0xEE`；要 WinUSB 绑定就不要删。

## 预设中的 stock/板级参数（18）

| 参数 | 作用 |
|---|---|
| `debug=0xc serial=3 cpus=6 keepsyms=1 -noprogress` | 启动/串口/符号调试 |
| `rd=ufsroot0 ufsroot=iosroot ufsrw=1 rootrw=1 sweethw=0 ufslun=2` | root 设备：UFS LUN 2，读写 HFS+ |
| `launchd_unsecure_cache=1 unentitled_ios_sim_launch=1 ignition_level=1` | 用户态 bring-up 门 |
| `wdt=-1 wdt_test=no_user_checkin` | bring-up 期间关闭看门狗 |
| `sweetfb_noconsole=1 sweetfb_hz=30` | 关闭 framebuffer console，30 Hz |
| `ufslogsecs=1` | UFS 日志计时 |

## 预设中的项目参数（26）

| 参数 | 默认 | 作用 |
|---|---|---|
| `rubyusb=1` | 0 | USB 总开关；以下 USB 路径都依赖它 |
| `rubyprobe=1` | 0 | vendor 探针通道 |
| `rubyep2log=0` | -1（ACM 默认） | EP2 日志流；0 关、1 开 |
| `rubypwrap=1`、`rubybatt=1`、`rubymt6360=1` | 0 | 板级：pwrap、电池、MT6360 |
| `rubkeys=1`、`rubyeint=1`、`rubyeintirq=1`、`rubykpdirq=1`、`rubyeintb1=1` | 0 | 按键与 EINT/IRQ 路径 |
| `rubyusbirq=1`、`rubyqmuirq=1` | 0 | USB IRQ 模式与 QMU done 中断 |
| `rubypad=1` | 0 | 时钟/pad 调节变体 |
| `rubydmauc=1` | 0 | 非缓存 DMA 环别名 |
| `rubyusbcmd=1` | 0 | EP0 命令通道 + ACM 命令模式 |
| `ruby_rxskip=1` | 0 | 只测 TX 时跳过 RX 路径 |
| `ruby_txreset=0` | 0 | stall 后的 TX 复位恢复 |
| `ruby_clr01=1` | 0 | CLEAR_FEATURE(0x01) 一致性处理 |
| `rubyreboot=1` | 0 | reboot-to-fastboot 路径 |
| `ruby_zlp=0` | 0 | MPS 整包时的 ZLP 尾包 |
| `ruby_enum=0` | -1（ACM 默认） | 描述符 profile 0/1/2 |
| `ruby_echo=1` | -1 | EP1 原始回显 |
| `ruby_iddump=1` | 0 | 启动时身份属性 dump |
| `rubywinusb=4` | 0 | MS OS 1.0 绑定（0 关、1–3 MS OS 2.0、4 MS OS 1.0） |
| `rubysetupdump=1` | 0 | SETUP 包追踪 |

## 不在预设中的 USB 驱动参数（分组）

默认值为编译默认；一次只改一个。完整解析见 `bsd/dev/ruby_usb.c` 的
`ruby_usb_probe()`。

### 队列几何

| 参数 | 默认 | 作用 |
|---|---|---|
| `ruby_txgpd` | 512 | 每 GPD 的 TX 字节数（64–16384，512 倍数） |
| `ruby_txgpd_num` | 64 | TX 环 GPD 槽数（8–64） |
| `ruby_rxgpd_num` | 16 | RX GPD 槽数（4–16） |
| `ruby_inflight` | 16 | 在飞 TX GPD 上限（1..环−1） |
| `ruby_rxbuf` | 512 | 每 GPD 的 RX payload 字节（64–16384） |
| `ruby_txslot` | 2 | TX FIFO slot 数（0–7）；slot=2 时每端点 3 units |
| `ruby_rxslot` | 2 | RX FIFO slot 数（0–7） |
| `ruby_txfbase` | 0 | TX FIFO 基址字节覆盖 |

### 端点选择（0334 线）

| 参数 | 默认 | 作用 |
|---|---|---|
| `ruby_txep` | 1 | TX 端点索引；只接受 1 与 3 |
| `ruby_rxep` | 1 | RX 端点槽 1–16（证据构建用过 2） |
| `ruby_fifo_plan` | 0 | 只读 FIFO 预算探针：打印 N units 的 fit/REJECT |
| `rubyep_test` | 0 | 0331 测试通道（`t331 …`，含 0334 `epmap/epall`） |

### QMU / 中断

| 参数 | 默认 | 作用 |
|---|---|---|
| `ruby_qstart_cfg` | 0 | 配置期就启动空 TX 环 |
| `ruby_qstart_keep` | 0 | 重配置时保持队列启动 |
| `ruby_qisar0_isr` | 0 | 在 ISR 里清 TX-done 位 |
| `ruby_qisar1_w` | 1 | 写 QISAR1 聚合位 |
| `ruby_qstart_ms` | 0 | 延迟 Q_START 时间 |
| `ruby_qstart_only` | 0 | 只做 Q_START、不做其余序列 |
| `ruby_lpmhrwe`、`ruby_lpmmask`、`ruby_lpm_fc` | 1/1/0 | LPM 与流控一致性位 |
| `ruby_usbintr`、`ruby_usb2parity` | 1/1 | vendor USB2 中断/一致性初始化 |

### TX 恢复与追踪

| 参数 | 默认 | 作用 |
|---|---|---|
| `ruby_txbell`、`ruby_txbell_ms` | 0 / 1 | TX 门铃轮询环 |
| `ruby_txreset`、`ruby_txeprst`、`ruby_tx_eprst_bit` | 0 / 0 / 0 | TX 复位策略与 EP_RST 位覆盖 |
| `ruby_txreplay` | 0 | 重建后重放未被取走的 GPD 负载 |
| `ruby_recover` | 0 | 恢复使能掩码（bit 0–2） |
| `ruby_clrhalt`、`ruby_clr81`、`ruby_devrst_pre`、`ruby_cfgrst` | 0 | clear-halt/设备复位变体（cfgrst 0–2） |
| `ruby_txfifo`、`ruby_txdone`、`ruby_noise`、`ruby_txdeq`、`ruby_txpio`、`ruby_txpiotail`、`ruby_dmareq_pio`、`ruby_qisar0_isr` | 0（txdone/txfifo 为 1） | 逐包追踪与 PIO 变体 |
| `rubyusb_hotplug`、`rubyusb_susp`、`rubyusb_window_ms` | 0 / 0 / 30000 | 0333 端口事件、suspend 门控、枚举窗口 |

## 镜像打包参数

| 环节 | 工具 | 参数 | 当前值 |
|---|---|---|---|
| payload | `.temp/mkpayload.py` | `kernel` | `kernel.development.sweet` |
| | | `adt` | 项目 `adt-identity.bin`（不在本仓库） |
| | | `out` | `payload-*.bin` |
| | | `--cmdline` | 上面三条预设之一（587/605/585 B） |
| | | `--ramdisk` | 常规路径不用（仅 `rd=md0` 救援） |
| boot 镜像 | `tools/image/pack_boot.py` | `--base` | stock/Magisk 128 MiB 镜像（外部） |
| | | `--shim` | 原始 loader shim（外部） |
| | | `--payload` | `mkpayload.py` 输出 |
| | | `--out` | `x16-*.img` |
| | | `--seed` | `0x84`（确定性填充） |
| | | `--payload-off` | 可选偏移覆盖 |
| | | `--expect-base-sha` / `--expect-shim-sha` / `--expect-payload-sha` / `--expect-out-sha` | 可选复现门禁 |
| 校验 | `tools/image/boot_verify.py` | image | 布局 + cmdline 打印 |

复现规则：同一 base/shim/payload 与同一 seed 重打包后用
`--expect-out-sha` 对比；0084 镜像因为当年用随机填充，无法逐字节复现
（可用 `boot_layout.py` 比较布局）。

## 参见

- [14 — USB 每端点队列](14-usb-per-endpoint.md)
- [11 — CI 基线与分支 pin](11-ci-baseline.md)
- [12 — USB 上位机通道](12-usb-host.md)
