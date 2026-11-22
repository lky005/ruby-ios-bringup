# ruby-ios-bringup

[English](README.md) · **中文**

[![xnu-0351](https://github.com/lky005/ruby-ios-bringup/actions/workflows/xnu.yml/badge.svg?branch=main)](https://github.com/lky005/ruby-ios-bringup/actions/workflows/xnu.yml)
[![host-checks](https://github.com/lky005/ruby-ios-bringup/actions/workflows/host-checks.yml/badge.svg?branch=main)](https://github.com/lky005/ruby-ios-bringup/actions/workflows/host-checks.yml)

一项研究性 bring-up：把 Apple 开源的 XNU 8796 内核与 iPhone X（iOS 16.7.16）
用户态移植到 MediaTek MT6877 平台（Redmi Note 12 Pro 5G，`ruby`）。设备保留
原厂引导链，`boot_b` 保留 TWRP 作为恢复路径。

仓库发布内核增量、构建配方、宿主侧工具与文档，不含 Apple 固件、IPSW、root
镜像或设备转储；完整哈希、run 历史与各子系统证据见
[STATUS](docs/records/STATUS.md) 与
[VERIFICATION](docs/records/VERIFICATION.md)。

## 状态

当前线：0351（`v0.9.0`）。保留 0349 的 USB/ECM 线，新增原生显示背光
（MT6877 DSI VM_CMD 直写 DCS `0x51`，γ2.6 LUT + 可抢占平滑）与 1 s
只读电池轮询。背光默认关闭，需 `rubybacklight=1 rubyblhw=1`；0351 启动行
已带上两者。v1.3 曲线仅在 console 验证；手感与夜览未获用户验收。

| 项 | 值 |
|---|---|
| 补丁集 | `bce06bba` —— 316 文件，CI 门禁 |
| 内核 | exec-data `9febbe97`（CI `45001473122`）；完整哈希见 VERIFICATION |
| 设备镜像 | `f0f7d454`（`x16-blv13.img`），440 B 启动行 |
| 标签 | `v0.9.0` / `p4-bl-batt-final` |

| 子系统 | 状态 | 说明 |
|---|---|---|
| CPU 与定时器 | 已验证 | 6× Cortex-A55，16 KiB 页，GICv3 |
| 存储 | 已验证 | UFS LUN 2，HFS+ root（`iosroot`）读写；4 MiB `md0` 救援 ramdisk |
| 显示 | 已验证 | 1080×2400 面板，经 IOSurface/IOMFB 驱动；原生背光滑条走 DSI DCS `0x51`（v1.2 已实测量手感；v1.3 曲线仅 console 验证） |
| 触摸 | 已验证 | Goodix GT9916R 走 SPI3，原生 EINT14 中断 |
| 实体按键 | 已验证 | 音量与电源键，经 KPD/TOPSTATUS 与 HID |
| 首启 | 已验证 | 锁屏到桌面；staged app 与小组件正常渲染 |
| USB 设备模式 | 已验证 | EP0 命令通道、MS OS 1.0 WinUSB 绑定、CDC-ECM 网卡（macOS/Linux 原生免驱；Windows 需经 usbipd-win + WSL2）+ SSH；0349 轮 64 MB wget 14.1 MB/s、TXRESET 0 |
| 电池与 Type-C | 只读 | MT6360 电压/状态遥测，1 s 轮询；拔电即清满电 latch；无充电控制 |
| Wi-Fi、蓝牙、蜂窝 | 未实现 | connsys 仅 stub |
| 音频、相机、GPU | 未实现 | — |
| 睡眠、RTC、USB host | 未实现 | — |

状态基于单台设备实测，见 [GUARANTEE](docs/records/GUARANTEE.zh.md)。已知边界：
背光 v1.3 手感与夜览恢复未获用户验收；电池触摸 A/B（`rubybattms=5000`）未做；
宿主侧 USB 数据仅在 `0x81` 通道实测；多端点并发与非默认端点 RX 未测；
`scp` 拉取会撞 FIFOFULL 半取窗口，大文件请走 HTTP。

## 系统架构

```text
原厂 LK（boot_a）
  → boot 镜像（内核 + ADT + shim）
  → XNU 8796 + MT6877 板级 HAL（UFS、显示、IRQ、USB/ECM）
  → iOS 16.7.16 用户态（SpringBoard）
```

1. Boot 镜像 —— `src/bringup/` 把内核、ADT 与 shim 打进原厂 LK 期望的
   128 MiB 几何；`boot_b`（TWRP）是恢复路径。
2. 内核增量 —— `patches/` 在 `xnu-8796.141.3` 上应用 MT6877 移植：中断路由、
   UFS 块 I/O、Goodix SPI3/EINT 触摸、MTU3 USB 设备栈与板级 HAL（按键、
   电池、pwrap）。集合内容固定，受哈希门禁。
3. 首启 —— `tools/image/` 在 dyld 层修补 LaunchServices 死锁（4 字节 ICL
   NOP），并在刷机前校验 root 与 boot 镜像完整性。

## 构建与验证

前置条件：

- 宿主：macOS 13.5 或更新，Xcode 16.0（CI 使用 `macos-15`）；宿主侧检查需
  Python 3.10 或更新。
- 目标机：已解锁 bootloader 的 Redmi Note 12 Pro 5G（`ruby`），`boot_b` 为
  TWRP，并自备 iPhone X iOS 16.7.16 IPSW 生成的 root。

```sh
# 1. 物化内容固定的基线（私有镜像；外部回退见下）
sh ci/prepare-baseline.sh <dest>
ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>

# 2. 宿主侧检查（只读，不接触设备）
python3 scripts/verify-local.py --ci-config config/0351.env

# 3. 复现内核
#    xnu-0351 workflow 从固定基线构建，校验 patchset 与 exec-data 哈希；
#    任一项目补丁被跳过即失败。
```

boot 镜像本身不在仓库内；`tools/image/` 提供离线校验与补丁工具。完整配方、
镜像打包与刷机见 [09-reproduce](docs/zh/09-reproduce.md)，恢复见
[08-recovery](docs/zh/08-recovery.md)。

## 文档

起点：[docs 索引](docs/README.md)
([English](docs/en/README.md) · [中文](docs/zh/README.md))。

| 部分 | 内容 |
|---|---|
| 架构（01–07） | SoC、引导链、显示、用户态、输入、硬件笔记 |
| 构建与 CI（08–11） | 恢复、复现、脚本、基线配方 |
| USB（12–14） | 宿主通道、EP2 黄金路径、按端点队列 |
| 记录 | [STATUS](docs/records/STATUS.md) · [VERIFICATION](docs/records/VERIFICATION.md) · [GUARANTEE](docs/records/GUARANTEE.md) |

```text
patches/   XNU 增量：UFS、触摸、按键、电池、USB/ECM
src/       boot 镜像打包、ARM64 shim、UFS 探针
tools/     宿主 USB 工具、镜像校验、SWEETLOG 解码、TWRP diff
ci/        固定基线配方、patchset pin、内核哈希门禁
config/    各线内核与启动参数配置
docs/      双语指南与记录
```

逐次硬件日志与探针卡放在独立仓库
[`lky005/ruby-ios-probes`](https://github.com/lky005/ruby-ios-probes)。项目历史
见 [STATUS](docs/records/STATUS.md) 与
[07-experiments](docs/zh/07-experiments.md)；0084 时期的演示视频与照片保留在
`media/`，采集规则见 [media/CAPTURE.md](media/CAPTURE.md)。

## 安全与范围

刷写实验性 boot 镜像并重划 `iosroot` 可能清空 Android `userdata`。操作前请务必
备份全部个人数据，并在刷机前阅读 [SAFETY](docs/records/SAFETY.md) 与
[SCOPE](docs/records/SCOPE.md)。双系统布局是方法记录，不是安装器。AMFI、
sandbox 与代码签名均已关闭，用户态不具备加固。

仓库不含 Apple 固件与个人数据。请勿在 issue 中发布或索取专有文件；见
[CONTRIBUTING](.github/CONTRIBUTING.md)。

## 许可证

原创代码与文档为 MIT。补丁修改 Apple XNU，仍受 APSL 2.0 约束。上游项目与
被排除材料见 [NOTICE](NOTICE)、
[ACKNOWLEDGEMENTS](docs/records/ACKNOWLEDGEMENTS.md) 与
[LEGAL](docs/records/LEGAL.md)。