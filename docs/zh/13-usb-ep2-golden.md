# 13 — USB EP2：状态机、黄金 PHY 与边界（0180–0195）

[English](../en/13-usb-ep2-golden.md) · **中文**

证据标签：**[实测]**、**[推断]**、**[历史]**。没有来源的数字视为 bug；
命令用占位符，不写个人路径。

## 范围

本章覆盖 ruby（MT6877）的设备态 USB EP2 bulk-IN 日志通道：0180–0189 的
QMU/环状态机线、0194 的黄金 PHY 值，以及通过 probe 通道测到的主机侧
行为。0195 是驱动文件头的双语致谢，仅改注释。

| 项 | 值 |
|---|---|
| 线 | 0195 |
| Patchset | 0194 `70597a6c…`（186 文件）；0195 `a9cc0050…`（187 文件） |
| 内核 | 0195 full `45ea1bc3…`、exec `6b22fc25…`（已验证不变）；0194 full `6d51fa71…` |
| 镜像 | 0195 `fe009b89…`（`x16-0195-ack.img`，已构建未刷）；0194 `1808e440…`（`x16-0194-golden-srctrl.img`） |
| Boot 门 | `RUBY USB: golden acr5=0x40805000`；14.1 s 枚举 |
| 未闭环 | XactErr 根因；512 B 聚合；主机端口稳定性 |

## 1. EP2 线修了什么

日志通道是一条 QMU bulk-IN 环：内核把 16 B 头 + 最多 495 B 文本写进日志
槽，16 B GPD 描述它，QMU 每槽发一个包。主机读 EP2 IN；坏事务表现为
EPIPE/XactErr。

| Patch | 单变量 | EPIPE 前帧数 | 判读 |
|---|---|---:|---|
| 0180 | QCR1 TX ZLP | 41 / 40 | 不是原因；XactErr 仍在 |
| 0181 | GPD clean 发布顺序 | 23 | 缓存顺序不是充分条件 |
| 0182 | GPD dump 钩子 | 14 | 钩子没在主机路径触发 |
| 0183 | dump 移到 `EP_RST` 前 | 3 | GPD 20–32 合法；无固定窗口 |
| 0184 | in-flight cap 16 | 37 | >16 失败；**ring-full 证伪** |
| 0185 | RX 眼图 6/3/2/13 + noise | 33 | **RX 眼图排除** |
| 0186 | HS TX slew 标定 | 1 | `fm_out=0`；走回退 |
| 0187 | vendor 顺序 + 板级眼图 | 21 | 顺序不是 FM 原因 |
| 0188 | `EP_RST` 后 state reset | 10 | QMU 留下 inactive |
| 0189 | stop → ring reset → start | 31 / 22 | `gap=0 inv=0`，QMU active |

[实测] 0189 是状态机修复：重置环之前先停 QMU，等 ACTIVE 前后各 flush
一次 `TX_FLUSHFIFO`，再启动队列。软件环与 QMU 保持同步；物理拔插会重跑
`CFG_IN / TXCFG_IN / EPRST_TX` 与 state reset，首读非零。

剩余失败在主机侧可见：随机帧数后出现
`USBD_STATUS_XACT_ERROR`（`0xC0000011`）。设备侧计数干净
（`TQERRIR0=0`、`gap=0`、`inv=0`、无 `TX_SENTSTALL`）。

## 2. 黄金 PHY（0194）

板级眼图为 `vrt=6, term=3, rev6=2, disc=13`（此前称为 "pre-emphasis"
的字段实为 PHY REV6）。取值遵循上游设备树绑定和板级
`ruby-mt6877.dtsi`。在线 SRCTRL 扫描：

| SRCTRL | ACR5 | 读到帧数 | 备注 |
|---:|---|---|---|
| 1 | `0x40801000` | 33, 4；31, 22 | 基线；方差大 |
| 4 | `0x40804000` | 3, 4；0186 的 1 | 差 |
| **5** | **`0x40805000`** | **21, 44；62 峰值** | 观测最佳 |
| 6 | `0x40806000` | 19, 13 | 干净，但低于 5 |
| 7 | `0x40807000` | 3, 7, 8 | 差；短帧 |

[实测] FM slew 标定在该端口从未起振（所有顺序/冷态试验 `fm_out=0`）。
0194 退役 FM，直接写 `ACR5=0x40805000`；boot 日志：

```
RUBY USB: PHY eye acr1=0x00846300 acr6=0x801004d2
RUBY USB: golden acr5=0x40805000
RUBY USB: IPPC ready (s1=0x00013d0f s2=0x00000001)
RUBY USB: EP2 state reset enq=0 deq=0 inflight=0 fifo_empty=1
```

62 帧是单次干净会话的峰值；分布很宽（4–62）。SRCTRL=5 是观测最佳值，
不是保证。

## 3. 主机侧行为

**帧长是可变的。** 一帧 = `16 B 头 + 最多 495 B 文本`；511 B 是上限，
不是固定长度。日志文本不足时帧就短。此前“短包 = FIFO 残留”的假设已被
证伪：完整 `CLEAR_FEATURE` 且 `fifo_empty=1` 之后，20 B 帧正好续在上一条
日志行之后，91 B 帧是 `EP2 no_log` 诊断（`total == pos`）。短帧是合法的
日志切片。

**大块读不聚合。** 4 KB/16 KB read 仍只返回一个 511 B 短包；511 B 相对
512 B maxpacket 是短包，短包立即终止 URB。聚合需要 512 B 帧，属于新的
帧封装改动。

**Pacing 不是原因。** 2 ms、5 ms、10 ms 都在随机 URB 数后失败（2–50）。
2 ms 反而跑出最长 50 帧；10 ms 没有稳定更长。失败是 per-URB，不是总线
热积累，也不是固定握手超时。

**透明续传只在端点级。** 标准 `CLEAR_FEATURE(0x82)` 能恢复端点并继续读；
连续 50–320 次 clear 后主机会停端口。XNU 内核活着（PHY 寄存器保持、
无 boot 横幅），但需要物理重新枚举。应用层 clear 救不了主机端口。

**ETW 只到通用错误。** 捕获到的 UCX 完成是
`USBD_STATUS_XACT_ERROR (0xC0000011)`；没有 CRC、toggle mismatch、STALL、
overrun 或 babble 细分。xHCI completion code 4 是重试后的通用
“transaction error”。细分需要 USB2 协议分析仪；ETW 给不了。

## 4. 复现

内核 CI 是内容固定的；镜像构建使用外部 base/shim/ADT，它们不在仓库里。
内核 full hash 是构建产物 pin；exec hash 才是可复现门——full-file hash
可能因 DWARF/路径元数据在不同 checkout 间不同。

```sh
# 内核：0195 仅注释，以 0194 的 exec pin 为参照
gh workflow run xnu.yml --ref <branch> \
  -f hash_config=config/0195.env \
  -f patchset_sha256=a9cc0050432d4259f38c2e5431e0ac05eecf95c3a78324ad94f11283d8031983

# 镜像（base/shim/ADT 由使用者提供）
python tools/image/pack_boot.py --base <base> --shim <shim> \
  --payload <payload> --out <image>

# 刷写与 boot 门（slot 用占位符；保留 recovery 镜像）
fastboot flash <slot> <image>
```

通过判据：`RUBY USB: golden acr5=0x40805000`、
`PHY eye acr1=0x00846300 acr6=0x801004d2`、枚举成功。
回滚：把上一版已验证镜像刷回 active slot；保留 recovery 镜像。

## 5. 边界

- XactErr（`0xC0000011`）未定性；ETW 无法细分。
- 511 B 短包帧封装无法大块聚合。
- 连续 clear 风暴可能停主机端口；内核活着但需要重新枚举。
- 62 帧是峰值样本，不是保证；0180–0195 是研究性 bring-up，不是稳定的
  USB function driver。

## Acknowledgements / 致谢

**English.** The MTU3/QMU and U2 PHY work in this chapter was developed
against public documentation (including upstream device tree bindings) and
cross-checked with the MediaTek vendor `mtu3`/`phy-mtk-tphy` drivers
(Linux 4.19, GPL-2.0) and the upstream Linux `mtu3` driver (GPL-2.0),
especially commit [`5aba179c34`](https://github.com/torvalds/linux/commit/5aba179c34)
("usb: mtu3: fix the failure of qmu stop") by Chunfeng Yun (MediaTek),
reported by Min Guo. The HS TX eye fields (vrt/term/rev6/disc; the field
earlier described as "pre-emphasis" is PHY REV6) follow the upstream
device-tree bindings and the board `ruby-mt6877.dtsi` values; the QMU stop
path uses the double `TX_FLUSHFIFO` sequence from that commit. Those trees
are references only and are not included in this repository; the driver is
original XNU glue and remains under APSL 2.0 as part of the XNU patches.

**中文。** 本章的 MTU3/QMU 与 U2 PHY 工作依据公开文档（包括上游设备树 YAML
绑定）开发，并与 MediaTek 厂商 mtu3/phy-mtk-tphy 驱动（Linux 4.19，
GPL-2.0）及上游 Linux mtu3 驱动（GPL-2.0）交叉核对，特别是 Chunfeng Yun
（MediaTek）的 [`5aba179c34`](https://github.com/torvalds/linux/commit/5aba179c34)
（"usb: mtu3: fix the failure of qmu stop"，Min Guo 报告）。HS TX 眼图字段
（vrt/term/rev6/disc；此前称为 "pre-emphasis" 的字段实为 PHY REV6）遵循
上游设备树绑定和板级 `ruby-mt6877.dtsi` 取值；QMU stop 路径采用该 commit
的双 `TX_FLUSHFIFO` 序列。上述源码仅作参考，未包含在本仓库中；驱动为原创
XNU 胶水实现，作为 XNU 补丁的一部分仍按 APSL 2.0 发布。

## 证据索引

- 公开记录：[STATUS](../records/STATUS.md)、
  [VERIFICATION](../records/VERIFICATION.md)、
  [ACKNOWLEDGEMENTS](../records/ACKNOWLEDGEMENTS.zh.md)。
- CI：`42295463255`（0194）、`42301546006`（0195 xnu）、`42302515812`
  （0195 host-checks）、rerun `42302694315`（exec pin 证明，success）。
- 本章是公开摘要；不链接私有运行卡。
