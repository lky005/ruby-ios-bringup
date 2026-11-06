# Acknowledgements

**English** · [中文](ACKNOWLEDGEMENTS.zh.md)

This project builds on open-source and community work. No upstream tree is
copied into this repository; the pinned baseline is fetched at build time.

## Upstream projects

- [ios-sweet](https://github.com/dipa-studio/ios-sweet) — the original
  iOS-on-Sweet project; the userland/display/UFS ideas and the patch lineage.
- [ios-topaz](https://github.com/MakrSas/ios-topaz) — the topaz port and the
  pinned build baseline.
- [blacktop/darwin-xnu-build](https://github.com/blacktop/darwin-xnu-build) —
  the MIT-licensed XNU build harness used by the workflow.
- [Apple XNU](https://github.com/apple-oss-distributions/xnu) — the open-source
  kernel; patches remain under APSL 2.0.
- [Xiaomi ruby-s-oss](https://github.com/MiCode/Xiaomi_Kernel_OpenSource) —
  the device tree and driver reference.
- [TWRP](https://twrp.me) — recovery environment; no TWRP image is included.
- [Magisk](https://github.com/topjohnwu/Magisk) — Android root; no Magisk image
  is included.

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

The iPhone X iOS 16.7.16 userland and Apple firmware belong to Apple. They are
not included; users must obtain their own copy and comply with Apple's terms.

## Tooling and assistance

Analysis, documentation and code review were assisted by LLM/agent tools,
including DeepSeek and other models. The author is responsible for all device
results; claims are backed by the artifacts, logs and hashes in this repository,
not by model output. LLM output is not a source of truth.

## Corrections

If an attribution is missing or wrong, open an issue with the exact file and
commit. Do not include personal or device-identifying data in the report.
