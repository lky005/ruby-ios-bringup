# 设备情况

[English](../en/device.md) · **中文**

这是设备描述，不是设备基线 hash 清单。GPT、`boot_a/b`、`vbmeta` 或分区
GUID 的 hash **有意不发布**：它们可能成为设备指纹。成功契约里的工件 hash
在 `config/0085.env`（`config/0084.env` 是上一合成上滑里程碑）。

## 这台机器

| 项 | 值 |
|---|---|
| 设备 | Redmi Note 12 Pro 5G，`ruby` / MT6877（天玑 1080） |
| 内存/存储 | 8 GB + 256 GB |
| 系统 | Android 12 / MIUI 13.0.4，已解锁，Magisk，slot `_a` |
| 分区布局 | `userdata` 208.4 GiB + `iosroot` 17 GiB；`boot_a` 128 MiB；`super` 约 9.1 GB |
| 当前状态 | `boot_a` 为 0084 XNU 镜像；Android 未恢复；`iosroot` 保留 ICL NOP |
| 成功工件 | 0085 真实触摸 boot 镜像/内核、0084 boot 镜像、root 镜像、ICL 块、boot cmdline |

## 必须匹配

- 固件和 GPT 布局（同一 `ruby` 机型类别）；
- root 镜像 hash 和 0085 真实触摸 boot 镜像 hash（0084 为上一里程碑）；
- `config/0085-boot.cmdline` 的启动参数（合成上滑镜像用 `0084-boot.cmdline`）；
- 面板/显示路径（1080×2400，LK 扫描层 `0x7cdfc000`）。

## 不需要匹配

触摸固件、Wi-Fi、USB、GPU、RTC 不属于成功路径。

## 测试状态

2026-10-22 在作者设备上跑过 0085 真实触摸启动（底边上滑解锁、双指
contact 分发、edge；用户态 pinch 未单独验证）、0084 进桌面和 CI 内核启动；
没有第二台/干净室回归。CI 只构建内核。
完整保证范围和暂缓项见 [`../../GUARANTEE.zh.md`](../records/GUARANTEE.zh.md)。
