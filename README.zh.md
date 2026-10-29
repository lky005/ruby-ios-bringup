# ruby-ios-bringup

[English](README.md) · **中文**

**在 MediaTek MT6877 手机上运行 XNU 8796 + iPhone X iOS 16.7.16 用户态。**
一个研究性 bring-up，以独立、脱敏的增量形式打包。

> **状态 2026-10-29：** 内核 CI 改为从内容固定的 82 文件基线（清单根
> `829d7598...`）拼装，基线由私有内容寻址镜像提供，0001-0079 不再是活的
> 上游依赖。ramdisk 线增加 LK ramdisk 救援根（`md0`，PID 1 进程内运行，
> 8/8 救援 `/etc/rc` 自检，USB `1209:0002` 枚举约 35 秒）；ramdisk 与 USB 两条线合并在
> `main` 上（由 `merge-ramdisk-usb-2026-10-29` 压缩合并）。
> `usb-0131b-probe-write` 保留厂商
> USB 探针；EP2 主机侧 XACT 仍未闭环。真实触摸（0085）仍是最后一个 UI
> 里程碑；本次 CI 改动没有刷入新的设备镜像。
>
> **状态 2026-10-22：真实触摸已通。** 0085 内核通过 GPIO bit-bang SPI3
> 驱动 Goodix GT9916R，能用真实底边上滑解锁，并把两个同时按下的 contact
> 和 edge 事件分发到 HID 层（内核 IOLog 证据；用户态 pinch 未单独加日志
> 验证）。0084 镜像和 CI 内核也都能到达锁屏并合成上滑进桌面。**计时从出现 Apple
> logo 开始：** B+NOP 首启观察到 22 秒到锁屏、30 秒 autoswipe；历史首启
> 约 58 秒，热重启约 22 秒。按键、USB、Wi-Fi、GPU、RTC 仍未通。
>
> **设备回归：** B+NOP 首启 -> A' 和 CI kernel 启动已在 2026-10-22 于作者设备
> 上跑过。第二台/干净室，以及从 IPSW 造 root/shim/ADT 的 builder 仍未完成。
> 见 [`GUARANTEE.zh.md`](GUARANTEE.zh.md)。

## 演示

[<img src="media/home-screen.jpg" width="360" alt="合成上滑后的 SpringBoard 桌面">](media/autoswipe.mp4)

**点击图片播放 12 秒片段**（720p60，2.6 MB）：锁屏 → 内核合成上滑 → 桌面。
2026-10-21 在 0084 构建上拍摄；已去除元数据和音轨。见
[`media/README.zh.md`](media/README.zh.md)。

仓库**不含 Apple 固件、iOS root、设备 dump 或 diff 数据**。内核由 Apple xnu
tag、内容固定的 82 文件基线 + 本项目增量构建；工作流会先校验还原出的树再
编译。

## 一览

| 领域 | 状态 |
|---|---|
| 启动 | stock LK → 128 MiB boot 镜像 → XNU 8796 → HFS+ root（UFS 或 `md0` 救援根） |
| CPU | 6× Cortex-A55，16K 页，GICv3，定时器 |
| 显示 | IOSurface/IOMFB → LK framebuffer，1080×2400 |
| 用户态 | launchd → lsd → backboardd → SpringBoard |
| 输入 | **真实 Goodix GT9916R**，bit-bang SPI3；解锁、双指 contact 上报、edge；0084 合成上滑仍保留 |
| 存储 | UFS LUN 2，`iosroot` 上读写 HFS+；4 MB HFS 救援根走 LK ramdisk 槽 |
| 最新 runs（分开记录） | 2026-10-29 救援根（8/8 救援 `/etc/rc` 自检）；真实触摸 0085 启动（harness 与 main-CI 重建）；0084 B+NOP 首启 -> A'（从 Apple logo 起 22 秒 / 30 秒） |
| 未闭环 | 第二台/干净室；从 IPSW 造 root/shim/ADT；严格 pin 的 payload；USB EP2 主机侧 XACT |
| 未通 | 按键、Wi-Fi、GPU、RTC；USB 仅探针 |
| 安全 | AMFI/sandbox/签名关闭；可能丢数据 |

## 这个里程碑的意义

难点不是“把 XNU 跑起来”，而是三处静默失败：LK 只接受的 128 MiB 镜像布局、
真正上屏的显示路径，以及一个看起来像内核 bug、实际卡在用户态
`MobileGestalt` 消费者的 LaunchServices 首启死锁。仓库记录精确字节、证据
和走过的弯路。

## 仓库结构

| 路径 | 内容 |
|---|---|
| `README.md`、`STATUS.md`、`SCOPE.md`、`SAFETY.md` | 入口与边界 |
| `ACKNOWLEDGEMENTS.zh.md`、`LEGAL.zh.md` | 致谢与法律风险声明 |
| `docs/en/`、`docs/zh/` | 英文与中文章节 |
| `touch/` | probe 阶梯、硬件契约与脱敏实验记录 |
| `patches/` | 自有 XNU 增量：0080 UFS、0085 Goodix 触摸、0086-0131b USB、0140/0141 ramdisk；历史 0081-0084 |
| `ci/` | 基线清单/recipe、固定 patchset 哈希、内核分段哈希与来源 |
| `config/` | 0140 ramdisk 与 0131b USB pin；0085 真实触摸和 0084 为历史 |
| `.github/workflows/xnu.yml` | 复现当前内核并校验 patchset/exec-data 哈希 |
| `src/bringup/` | 早期启动 payload、shim、镜像打包 |
| `src/ufs-probe/` | MT6877 UFS 只读探针 |
| `tools/image/` | ICL 补丁、dyld 扫描、boot 校验 |
| `tools/twrp/` | 已验证的块 diff/patch（TWRP）和 host CRC/target 辅助脚本 |
| `tools/sweetlog/` | SWEETLOG ring 解码器 |
| `scripts/` | 基线拉取、本地验证 |
| `media/` | 脱敏演示片段、桌面照片与拍摄规范 |
| `ruby-ios-probes` | 独立的公开探针/run-card 仓库（不含 Apple 材料） |

## 探针 / 测试实验室

环境和设备测试记录放在独立的公开仓库：
[`ruby-ios-probes`](https://github.com/lky005/ruby-ios-probes)。

为什么分开：

- 本仓库是稳定的配方/契约（patch、CI、boot 镜像 pin、hash）；
- 探针仓库放 host/device 检查、run card、hash 稳定性说明，每次 run 都会变；
- CI 分开，环境探针失败不会影响内核构建。

本仓库仍是配方和 hash 的唯一事实源；探针仓库只记录探针和测试。两边都不含
Apple 材料。

## 构建与验证

```sh
# 主机检查：不碰设备、不写镜像
python scripts/verify-local.py

# host 侧 diff/restore 辅助（对源镜像只读）
python tools/twrp/make_crc_map.py <image> <map>
python tools/twrp/make_target_patch.py <image> <idx> <patch> --crc-map <map>

# SWEETLOG ring 解码（host）
python tools/sweetlog/decode.py <area.bin> <out.txt>
```

内核工作流使用：

```text
apple:    apple-oss-distributions/xnu @ xnu-8796.141.3 (f625db25...)
baseline: 82 文件（sweet 0001-0079），清单根 829d7598...
recipe:   ci/prepare-baseline.sh（私有镜像；公开回退 ALLOW_PUBLIC_UPSTREAM=1）
patchset: 27894e7b...（main，137 文件；USB 分支 29449e32...，135 文件）
runner:   macos-14 / Xcode 15.0.1 / macOS 13.5 xnu
config:   DEVELOPMENT, MACHINE_CONFIG=SWEET, -mcpu=cortex-a55
```

recipe 校验 82 文件基线、加入本项目补丁、应用 0010/0012 小改动、统一换行；
patchset 哈希不匹配就停止。boot 镜像本身**不在**仓库里；`tools/image/`
提供离线校验和补丁工具。详见 `docs/zh/11-ci-baseline.md`。

Host 管线（不碰设备、不碰 root）：`scripts/test-pipeline.sh`，输入 base
boot、kernel、ADT、shim 和 0084 golden；生成 payload、确定性 boot 镜像并
校验布局；见 `docs/zh/09-reproduce.md`。

## 设备情况

| 项 | 值 |
|---|---|
| 设备 | Redmi Note 12 Pro 5G，`ruby` / MT6877，8 GB + 256 GB |
| 系统 | Android 12 / MIUI 13.0.4，已解锁，Magisk，slot `_a` |
| 布局 | `userdata` 208.4 GiB + `iosroot` 17 GiB；`boot_a` 128 MiB；`super` 约 9.1 GB |
| 当前状态 | 工件：真实触摸 0085 镜像/内核、0084 镜像、root A/A' 快照、ICL 块、boot cmdline；设备不在本仓库内 |
| 成功工件 | 0085 镜像、内核、root A/A' 快照、ICL 块、boot cmdline |
| 需匹配 | 固件/GPT、root hash、boot 镜像、启动参数、面板/显示 |
| 不需要 | 触摸固件、Wi-Fi、USB、GPU、RTC |

root 状态（外部；pin 在 `config/0085.env`）：

| 状态 | SHA-256 | 含义 |
|---|---|---|
| A 成功快照 | `e698339d...` | boot22 之后；ICL NOP + 首启状态 |
| B 首启前 | `985c30...` | pulled+seeded；ICL 原块；boot22 diff 把 B -> A |
| C clean 基础 | `34c2882d...` | mkiosroot + tweaks；还需要首启/seed |
| A' 首启快照 | `55e2ab2c...` | 一次 B+NOP 首启快照；新的首启会不同 |

设备基线哈希（GPT/boot/vbmeta）**不发布**，因为可能成为设备指纹；工件
hash 在 `config/0085.env`。见 [`docs/zh/device.md`](docs/zh/device.md)。

## 边界与安全

- 默认路径会写 iOS root，可能清掉 Android 数据。**按会丢数据准备。**
- 双系统布局只是附录**方法说明**，不是安装器。
- 不含 Apple 固件，不连 Apple 激活服务器，不放个人数据。
- 刷机前读 [`SAFETY.md`](SAFETY.md) 和 [`SCOPE.md`](SCOPE.md)。
- 内容政策：不要发布或索要 Apple 固件、iOS root、dyld 缓存、设备 dump、
  序列号/IMEI/MAC 或个人信息。见 issue 模板
  （`.github/ISSUE_TEMPLATE/`）和 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 保证

成功路径——启动到锁屏、合成上滑到桌面——现在有**单台设备证据**（B+NOP 首启
-> A'、CI kernel 启动）和文档化配方。它不是第二台/干净室保证。启动前工件
hash 对命名文件是固定的；启动后的 live-root/ring/日志 hash 易变。从 IPSW
造 root/shim/ADT 的 builder 和严格 pin 的 payload 仍未完成。见
[`GUARANTEE.zh.md`](GUARANTEE.zh.md)。

## 文档

从 [`docs/README.md`](docs/README.md) 开始，或直接进入
[English chapters](docs/en/README.md) / [中文章节](docs/zh/README.md)。

## 致谢与法律

见 [`ACKNOWLEDGEMENTS.zh.md`](ACKNOWLEDGEMENTS.zh.md) 和
[`LEGAL.zh.md`](LEGAL.zh.md)。媒体拍摄规范见
[`media/CAPTURE.zh.md`](media/CAPTURE.zh.md)。

## 许可

自有代码与文档 MIT；XNU 补丁按 APSL 2.0；上游与排除内容见
[`NOTICE`](NOTICE)。

**上游声明：** `ios-sweet` 和 `ios-topaz` 在固定 commit 上**没有 LICENSE
文件**。本仓库不包含完整上游树；发布 recipe、本项目补丁，以及已披露的
`ci/baseline-changes.patch`（0010/0012 改动）；不声称已获得上游许可。
见 [`LEGAL.zh.md`](LEGAL.zh.md)。
