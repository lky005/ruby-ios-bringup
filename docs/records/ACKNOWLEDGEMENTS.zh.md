# 致谢

[English](ACKNOWLEDGEMENTS.md) · **中文**

本项目建立在开源和社区工作的基础上。仓库不 vendor 上游树；构建时按固定
commit 拉取基线。

## 上游项目

- [ios-sweet](https://github.com/dipa-studio/ios-sweet) — 原始
  iOS-on-Sweet 项目（dipa-studio）；用户态/显示/UFS 思路和补丁谱系。
- [ios-topaz](https://github.com/MakrSas/ios-topaz) — topaz 移植和构建基线
  （MakrSas，ios-sweet 的 fork）。
- [HakiOS-MTK](https://github.com/oosexgang/hackios-xnu-kernel) — oosexgang
  的 MediaTek XNU bring-up（同一账号下的 kernel/userland 仓库）。用于
  KPD/pwrap/connsys 与数据卷决策的**只读对比**；其内核驱动为 APSL-2.0。
  0150/0169 按键按 Xiaomi DTS 与 vendor `kpd.c` 实现；路线图中计划改编的
  `redwood_mtkkeys.c` **未采用**，未复制任何代码。
- [blacktop/darwin-xnu-build](https://github.com/blacktop/darwin-xnu-build) —
  workflow 使用的 MIT 许可 XNU 构建框架。
- [Apple XNU](https://github.com/apple-oss-distributions/xnu) — 开源内核；
  补丁按 APSL 2.0。
- [Xiaomi ruby-s-oss](https://github.com/MiCode/Xiaomi_Kernel_OpenSource) —
  厂商 4.19.191 `ruby-s-oss` 树（MiCode），设备树与驱动参考。
- [TWRP](https://twrp.me) — recovery 环境；仓库不含 TWRP 镜像。
- [Magisk](https://github.com/topjohnwu/Magisk) — Android root；仓库不含
  Magisk 镜像。

### USB device-mode driver / USB 驱动

**English.** The USB device-mode driver (`bsd/dev/ruby_usb.c`) was developed
against public documentation (including upstream device tree bindings) and
cross-checked with the MediaTek vendor `mtu3`/`phy-mtk-tphy` drivers
(Linux 4.19, GPL-2.0) and the upstream Linux `mtu3` driver (GPL-2.0),
especially commit [`5aba179c34`](https://github.com/torvalds/linux/commit/5aba179c34)
(“usb: mtu3: fix the failure of qmu stop”) by Chunfeng Yun (MediaTek),
reported by Min Guo. The HS TX eye fields (vrt/term/rev6/disc; the field
earlier described as “pre-emphasis” is PHY REV6) follow the upstream
device-tree bindings and the board `ruby-mt6877.dtsi` values; the QMU stop
path uses the double `TX_FLUSHFIFO` sequence from that commit. Those trees
are references only and are not included in this repository; the driver is
original XNU glue and remains under APSL 2.0 as part of the XNU patches.

**中文。** USB device-mode 驱动（`bsd/dev/ruby_usb.c`）依据公开文档（包括
上游设备树 YAML 绑定）开发，并与 MediaTek 厂商 mtu3/phy-mtk-tphy 驱动
（Linux 4.19，GPL-2.0）及上游 Linux mtu3 驱动（GPL-2.0）交叉核对，特别是
Chunfeng Yun（MediaTek）的 [`5aba179c34`](https://github.com/torvalds/linux/commit/5aba179c34)
（“usb: mtu3: fix the failure of qmu stop”，Min Guo 报告）。HS TX 眼图字段
（vrt/term/rev6/disc；此前称为 “pre-emphasis” 的字段实为 PHY REV6）遵循
上游设备树绑定和板级 `ruby-mt6877.dtsi` 取值；QMU stop 路径采用该 commit
的双 `TX_FLUSHFIFO` 序列。上述源码仅作参考，未包含在本仓库中；驱动为原创
XNU 胶水实现，作为 XNU 补丁的一部分仍按 APSL 2.0 发布。

**0333/0334 line.** Port events, per-endpoint GPD rings and the FIFO
allocation follow the same references. The segment rules —
`roundup_pow_of_two(ceil(mps / 512))` 512-byte units times `(slot + 1)`, the
`FIFOADDR`/`FIFOSEGSIZE` encoding, the per-endpoint CSR stride and the
`BIT(0) << ep` TX-done bit — mirror the vendor `ep_fifo_alloc()` /
`mtu3_config_ep()` / `mtu3_qmu_start()` logic in the MediaTek 4.19 `mtu3`
driver and the upstream Linux driver. Those trees are references only; no
vendor code is copied, and the original XNU glue stays under APSL 2.0.

**0333/0334 线。** 端口事件、每端点 GPD 环与 FIFO 分配沿用同一组参考：
512 B 段的 `roundup_pow_of_two(ceil(mps / 512)) × (slot + 1)` 规则、
`FIFOADDR`/`FIFOSEGSIZE` 编码、每端点 CSR 步长与 `BIT(0) << ep` 的 TX done
位，均对应 MediaTek 4.19 `mtu3` 与上游 Linux 驱动的
`ep_fifo_alloc()` / `mtu3_config_ep()` / `mtu3_qmu_start()` 逻辑。上述源码
仅作参考，未复制任何厂商代码；原创 XNU 胶水仍按 APSL 2.0 发布。

iPhone X iOS 16.7.16 用户态和 Apple 固件归 Apple 所有，仓库不包含；使用者
需自备并遵守 Apple 条款。

## 工具与协助

分析、文档和代码审阅使用了 LLM/agent 工具，包括 DeepSeek 及其他模型。作者
对所有设备结果负责；结论以仓库里的工件、日志和 hash 为准，不以模型输出为
准。LLM 输出不是事实来源。

## 更正

如果致谢遗漏或写错，请带文件和 commit 开 issue；不要在报告里放个人或设备
标识数据。
