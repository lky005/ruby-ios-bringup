# 14 — USB 每端点队列与 FIFO 分配（0333–0334）

**中文** · [English](../en/14-usb-per-endpoint.md)

> 状态标注沿用[仓库 README](../../README.zh.md)。没有来源的数字视为
> bug；命令用占位符，不写个人路径。本章讲 device 模式队列；上位机通道
> 见 [12](12-usb-host.md)，0180–0195 的 EP2 历史见 [13](13-usb-ep2-golden.md)。

## 范围

0333/0334 建立在 0195 的 EP2 状态机之上：

- **0333** — 控制器事件（LINK 速率变化、MAC2 suspend/resume）、统一端口
  状态机（reattach 归 workloop）、门控的 U2 suspend 冻结。开关
  `rubyusb_hotplug=1`、`rubyusb_susp=1`，默认均为 0。
- **0334** — 每个端点槽独立 GPD 环、按 vendor 步长的每端点 CSR/QMU/HIAR
  偏移、FIFO 预算探针升级为实际分配。通过 0331 通道的新命令
  `t331 epmap / eptx / eprx / epall` 验证。

## 已验证（2026-11-18）[实测]

构建与 pin：

| 项 | 值 |
|---|---|
| Patchset | `d87e666f…`（305 文件） |
| CI | `xnu-0334` run `44296779724`（成功） |
| CI 内核 | full `5ee3019d…`、exec-data `61c6b1a1…`（`config/0334.env`） |
| 设备镜像 | default `561f1026…`（587 B cmdline）、lite `b4b95789…`（585 B，`rubyep_test=1`） |

设备运行（先 lite，后 default）：

1. 0331 lite 矩阵 **PASS** — T0/T1/T3/T4；512/1024/4096/16384 B 全部
   `DATA-OK` + `CRC-OK`。
2. `t331 epmap` — TX/RX 均给 EP1–5 分配
   `0x0 / 0x600 / 0xc00 / 0x1200 / 0x1800`，EP6–8 拒绝：
   ```
   RUBY CFG: 0334b4 epfifo tx ep1 addr=0x0 units=3
   ...
   RUBY CFG: 0334b4 epfifo tx ep6 REJECT units=3 free=1
   ...
   RUBY CFG: 0334b4 epfifo tx_free=1 rx_free=1 ep0_cap=512
   ```
3. `t331 epall 511` — mailbox
   `ok_tx=3e tmo_tx=00 err_tx=1c0 ok_rx=3e err_rx=1c0 restore=0`；设备逐行
   `st=0`：
   ```
   RUBY EP TEST: 0334b4 epall tx ep=1 addr=0x0 st=0
   ... tx ep=5 addr=0x1800 st=0
   RUBY EP TEST: 0334b4 epall rx ep=1 addr=0x0 st=0
   ... rx ep=5 addr=0x1800 st=0
   RUBY EP TEST: 0334b4 epall done ok_tx=3e tmo_tx=00 err_tx=1c0
   ok_rx=3e err_rx=1c0 restore=0
   ```
4. RX 每槽独立环，结束后恢复默认：
   ```
   RUBY USB: 0334b3 rx ring sel=1 pa=0x1420f0000 uc
   RUBY USB: 0334b3 rx ring sel=2 pa=0x1420f4200 cached
   RUBY USB: 0334b3 rx ring sel=3 pa=0x1420f4300 cached
   RUBY USB: 0334b3 rx ring sel=4 pa=0x1420f4400 cached
   RUBY USB: 0334b3 rx ring sel=5 pa=0x1420f4500 cached
   RUBY USB: 0334b3 rx ring sel=1 pa=0x1420f0000 uc   （恢复）
   ```
5. 批量后 lite 矩阵再次 **PASS** — EP1 恢复保证默认数据通路存活。
6. 默认镜像：`0334b3 rx ring sel=1 uc`，启动**没有** `0334b4 epfifo` 行，
   WinUSB `CM_PROB_NONE`，无 panic，`fused=0`。

## 设计

### 每槽环

- TX：slot 1 保留已验证的 BSS/UC 1 KB 环；其他槽各用自己的缓存 1 KB 环
  （`ruby_gpd_ring_slots[16]`）。
- RX：slot 1 保留页对齐 BSS/UC 环；其他槽各用自己的缓存 256 B 环。
  payload buffer 仍共享，同一时刻每方向只有一个环承载流量。

### 每端点寄存器

偏移按 vendor 步长（mtu3 `MU3D_EP_TXCR/RXCR`、`USB_QMU_TQ/RQ`）：

| 寄存器 | 公式 |
|---|---|
| TX CSR0/1/2 | `0x0110 + (ep-1)*0x10`（+0/+4/+8） |
| TX TQ CSR/SAR/CPR | `0x0510 + (ep-1)*0x10`（+0/+4/+8） |
| TX HIAR | `0x0484 + (ep-1)*4` |
| RX CSR0/1/2 | `0x0210 + (ep-1)*0x10`（+0/+4/+8） |
| RX RQ CSR/SAR/CPR | `0x0610 + (ep-1)*0x10`（+0/+4/+8） |
| RX HIAR | `0x04c4 + (ep-1)*4` |
| TX done 位 | `BIT(0) << ep` |

### FIFO 分配

`ruby_epfifo_map()` 对应 vendor `ep_fifo_alloc()`：

- 512 B 为单位；`units = roundup_pow_of_two(ceil(mps / 512)) * (slot + 1)`。
- 本机以 slot 2 运行（TWRP dump 里 EP2 在字节 1536），所以每端点 3 units，
  单方向 `16 / 3 = 5` 个端点。
- `CSR2 = FIFOADDR(addr >> 4) | FIFOSEGSIZE(ilog2(512))`；EP0 有独立的
  `CAP_EP0FFSZ` 块，因此每方向池从地址 0 开始。
- EP6–8 打印 REJECT，而不是让段重叠。

### IRQ 模式下的完成判据

`rubyqmuirq=1` 时 1 ms QMU 路径可能先消费并清掉 QISAR0 done 位，因此以
`TQCPR` 前进为主判据，done 位为备。

## 保留的负结果

0334b4 首版用 `fifo_addr == 0` 当“未分配”哨兵。EP1 的段地址合法就是 0，
于是 EP1 失败：`ok_tx=3c err_tx=1c2 ok_rx=3c err_rx=1c2`、`st=22`。改用显式
`0xffffffff` 哨兵后通过；上面的数据都是修复版。

## 复现

```sh
# lite 镜像必须带 rubyep_test=1（见启动参数附录）
python tools/host/ruby_usb_ep_test.py --matrix lite
python tools/host/ruby_usb_ep_test.py --cmd "t331 epmap"
python tools/host/ruby_usb_ep_test.py --cmd "t331 epall 511"
python tools/host/ruby_usb_ep_test.py --matrix lite   # 恢复检查
```

预期：矩阵 PASS、分配 `0x0/0x600/0xc00/0x1200/0x1800`、EP6–8 `REJECT`、
`ok_tx/ok_rx = 0x3e`、`err = 0x1c0`、`restore = 0`。

## 边界（不担保）

- 上位机工具固定 `0x81`，EP2–8 只有 QMU 侧证据，没有宿主可见的数据校验。
- RX 槽只证明 arm + `RQCSR` START；宿主不向非默认 OUT 端点写数据。
- 每方向 5 个端点是容量结论；多端点并发互扰未测。
- 能放下 8+8 的 slot=1 变体未测试。
- 本轮未重测 selective suspend 与热插拔；0333 证据仍为 10/10 重枚举与
  两次 suspend。

## 参见

- [12 — USB 上位机通道](12-usb-host.md)
- [13 — EP2 状态机（0180–0195，历史）](13-usb-ep2-golden.md)
- [附录 — 启动参数与打包](appendix-bootargs.md)
