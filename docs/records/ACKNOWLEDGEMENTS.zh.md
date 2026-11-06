# 致谢

[English](ACKNOWLEDGEMENTS.md) · **中文**

本项目建立在开源和社区工作的基础上。仓库不 vendor 上游树；构建时按固定
commit 拉取基线。

## 上游项目

- [ios-sweet](https://github.com/dipa-studio/ios-sweet) — 原始
  iOS-on-Sweet 项目；用户态/显示/UFS 思路和补丁谱系。
- [ios-topaz](https://github.com/MakrSas/ios-topaz) — topaz 移植和构建基线。
- [blacktop/darwin-xnu-build](https://github.com/blacktop/darwin-xnu-build) —
  workflow 使用的 MIT 许可 XNU 构建框架。
- [Apple XNU](https://github.com/apple-oss-distributions/xnu) — 开源内核；
  补丁按 APSL 2.0。
- [Xiaomi ruby-s-oss](https://github.com/MiCode/Xiaomi_Kernel_OpenSource) —
  设备树和驱动参考。
- [TWRP](https://twrp.me) — recovery 环境；仓库不含 TWRP 镜像。
- [Magisk](https://github.com/topjohnwu/Magisk) — Android root；仓库不含
  Magisk 镜像。

iPhone X iOS 16.7.16 用户态和 Apple 固件归 Apple 所有，仓库不包含；使用者
需自备并遵守 Apple 条款。

## 工具与协助

分析、文档和代码审阅使用了 LLM/agent 工具，包括 DeepSeek 及其他模型。作者
对所有设备结果负责；结论以仓库里的工件、日志和 hash 为准，不以模型输出为
准。LLM 输出不是事实来源。

## 更正

如果致谢遗漏或写错，请带文件和 commit 开 issue；不要在报告里放个人或设备
标识数据。
