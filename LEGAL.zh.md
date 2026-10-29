# 法律与风险声明

[English](LEGAL.md) · **中文**

**这不是法律意见。** 各地法律不同；公开再分发或商业使用前请咨询合格律师。

## 这个仓库是什么

一个研究与互操作记录：在用户自己拥有的设备上运行开源内核和用户自备的
iOS 用户态。仅供学术研究与互操作研究使用，不是产品，不提供任何保证。
与 Apple、小米、MediaTek、上游项目及其关联方无隶属关系。

## 不含 Apple 二进制

仓库**不包含** Apple 固件、IPSW/DMG、iOS root、dyld 共享缓存或 Apple
用户态二进制。地址、偏移和短反汇编窗口是事实记录。使用者需自行取得
Apple 材料并遵守 Apple 条款。

## 补丁与上游许可

- `patches/` 修改 Apple XNU，按 APSL 2.0。
- `ios-sweet` 和 `ios-topaz` 在固定 commit 上**没有 LICENSE 文件**。仓库
  不把上游树复制进来，也不公开完整 delta。recipe 拉取上游树，应用
  `ci/baseline-changes.patch`（0010/0012 的小改动）和本项目补丁。CI 从私有
  内容寻址镜像取基线；只发布清单根与已披露的 0010/0012 改动，不分发完整
  上游补丁。公开再分发前，请取得上游作者许可，或让仓库保持私有。
- TWRP 和 Magisk 是 GPL；仓库不含它们的镜像。

## 逆向与规避

仓库记录了用户态 `InstalledContentLibrary` NOP、关闭 AMFI/sandbox/签名，
以及研究中使用的 shared-cache 偏移。逆向和反规避规则差异很大（例如美国
DMCA §1201 及各地法律）。

项目**不提供** Apple 激活、DRM 或账号绕过，也不连接 Apple 服务器。不要
用于盗版、未授权访问或绕过他人设备保护。公开或商业使用前先做法律审查。

## 设备风险

解锁、刷机、改分区、raw block 写可能导致保修失效、数据丢失或变砖。没有
任何保证；按会丢数据来准备。

## 商标

Apple、iPhone、iOS、小米、Redmi、MediaTek 等名称归各自所有者；这里仅用于
识别和兼容性说明。

## 隐私

仓库不含序列号、IMEI、MAC、Apple 账号数据或个人路径；不要添加。媒体在
提交前必须按 `media/CAPTURE.md` 脱敏。
