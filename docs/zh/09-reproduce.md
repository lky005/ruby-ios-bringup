# 09 — 复现

[English](../en/09-reproduce.md) · **中文**

> 成功路径范围、bundle hash 和不保证项见
> [`../../GUARANTEE.zh.md`](../../GUARANTEE.zh.md)。

内核构建可复现；boot 镜像和 iOS root 不是完全自包含：Apple 用户态不可
分发，0085/0084 镜像用了上游 shim/loader/ADT 构建器，而它不在仓库里。这一章
说明哪些能从仓库复现，哪些要自备。

## 需要自备

- 已解锁的 `ruby`（Redmi Note 12 Pro 5G / MT6877），Android 12。
- iPhone X iOS 16.7.16（20H392）IPSW 和 iOS root 镜像。
- 已知可启动的完整 128 MiB Magisk/stock boot 镜像（恢复用）。
- `ruby` 的 A12 TWRP（离线 I/O）。
- 一个可用 macOS runner 的 GitHub 账号。

## 构建内核

`.github/workflows/xnu.yml` 运行 `ci/prepare-baseline.sh`。recipe 取 82 文件
基线（私有镜像；`ALLOW_PUBLIC_UPSTREAM=1` 是外部回退）、校验清单根、加入本
项目补丁、应用 0010/0012 小改动、统一换行；patchset 哈希不匹配就停止。镜像/
密钥边界见 [`11-ci-baseline.md`](11-ci-baseline.md)。公开回退可用
`ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>`。

```text
apple:    apple-oss-distributions/xnu @ xnu-8796.141.3 (f625db25...)
baseline: 82 文件（sweet 0001-0079），清单根 829d7598...
recipe:   ci/prepare-baseline.sh（不复制上游树）
patchset: 27894e7b...（main，137 文件）
          USB 分支：29449e32...（135 文件），config/0131b.env
dxb:      blacktop/darwin-xnu-build @ 663906528d1cd5ea8fde7de6f16de73db9511549
runner:   macos-14, Xcode 15.0.1, macOS 13.5 xnu
config:   DEVELOPMENT, MACHINE_CONFIG=SWEET, -mcpu=cortex-a55
```

main 构建 ramdisk/0140 集，包含到 0131b 的 USB 系列。下面的 0086/0085
引用是历史记录。

从 **Actions → xnu → Run workflow** 运行，或推送 `ci/`、`patches/`、
`config/`、workflow 的改动。产物：`xnu-kernel`、`xnu-buildtree`。

## 救援根（2026-10-29）

ramdisk 线在 LK ramdisk 槽放一个 4 MB HFS+ root。内核用 `rubyrdsz=` 导入
并挂成 `md0`；PID 1 进程内跑 `/etc/rc` 和 applet，不依赖 launchd 或
fork/exec。救援镜像（`6795d9e4...`；B1 为 `49a10e49...`）和 root 是外部
输入；完整 Unix/iOS 环境仍在 UFS iOS root。

## Host pipeline

host 管线只用 <1 GiB 工件，不碰 16 GiB root。shim 和 ADT 是外部输入；
上游 payload 工具按固定基线 commit 拉取。

```sh
sh scripts/build-payload.sh --kernel <kernel> --adt <adt> \
  --cmdline-file config/0085-boot.cmdline --out <payload.bin>

python tools/image/pack_boot.py --base <magisk.img> --shim <Image> \
  --payload <payload.bin> --out <boot.img>

python tools/image/boot_layout.py --image <boot.img> \
  --config config/0085.env --payload <payload.bin> --base <magisk.img>
```

`--golden <boot.img>` 是可选的；没有 golden 镜像时，config pin 足够做外部
校验。root 单独按 [`root-recipe.md`](root-recipe.md) 准备。

上面三条命令是 0085 路径；`scripts/test-pipeline.sh` 是 0084 里程碑的
harness，固定用 `config/0084.env`，默认不测试 0085。

0085 真实触摸输入产出的 payload 是
`dbc57e96396f2e3e23213a76d300b1a329e2b4a320bc7363cf99ce0fc9e52b1c`。
实机镜像 `ace60d16...`；CI 重建内核打包出的镜像
`54d1b306...`（未刷）。这些镜像用了随机 filler，重建时请校验布局而不是
镜像 SHA。

上一里程碑：0084 输入产出 payload `50701e81...`，seed `0x84` 重建为
`a0ce0fe1...`，与 `94c639d1...` 布局等价但非字节一致。

2026-10-22：B+NOP 首启 -> A' 和 CI kernel 启动已在作者设备上跑过。CI kernel
用了 payload ref `33852e3`，不是 pin `5095ac1`。A' 是首启快照；第二台/
干净室仍未做。

## 打包 boot 镜像

0085/0084 镜像使用上游 loader/ADT 构建器（本轮实验用外部 ruby-loader 工具）。
仓库有早期 `src/bringup` 打包器和离线校验器，但没有上游 loader 源码。
完整重建请用基线的 `shim/` 和 `tools/`，或自备打包器。

必须满足：

- 完整 128 MiB；DTB/AVB0/AVB footer 保持 stock 偏移。
- kernel 槽精确 16,606,685 B（FEXTRA 补齐，无尾部零）。
- payload 在预期入口；保留 ARM64 Image 头。
- 刷前用 `tools/image/boot_verify.py` 校验。

## 刷写

刷写把整个 128 MiB 镜像写进 `boot_a`，不改 root 分区。保留 Magisk/stock
和 TWRP 镜像；b 槽不可用。

```sh
adb reboot bootloader
fastboot devices
fastboot flash boot_a <boot.img>
# slot _a 已激活；旧 fastboot 可能不认 --set-active
fastboot reboot
```

## 启动参数

`config/0085-boot.cmdline` 是真实触摸的 cmdline。关键参数：

| 参数 | 作用 |
|---|---|
| `cpus=6` | 6 个 A55 |
| `ufsroot=iosroot`、`ufslun=2`、`ufsrw=1`、`rootrw=1` | root 设备 |
| `sweetfb_noconsole=1`、`sweetfb_hz=30` | 显示/调试 |
| `sweetgt=1` | 启用 Goodix 驱动；`0` 关闭 |

0084 合成上滑里程碑用 `config/0084-boot.cmdline` 和
`sweetautoswipe=90000`、`sweetautoswiperetry=15000`、
`sweetautoswipeattempts=3`；0085 去掉这些，只让真实触摸驱动 UI。

## 预期现象

- 所有计时从出现 Apple logo 开始。打补丁后的首次启动约 58 秒；热重启约
  22 秒（boot23）。2026-10-22 的 B+NOP 首启从 Apple logo 起观察到 22 秒到
  锁屏、30 秒 autoswipe（cache-warm；观察值，不是固定时序）。上游首启
  4–5 分钟。
- 锁屏：日期从 12 月 31 日开始（无 RTC/NTP），时钟会走；有相机图标和
  Home Bar。
- 真实底边上滑解锁到桌面（0085）；两个 contact 会分发到 HID，edge 正常；
  用户态 pinch 未单独加日志验证。0084 合成上滑也可解锁。
- 可能有黑壁纸、`Waiting...` widget、Messages badge。
- 0085 内核真实触摸已通（底边上滑解锁、双指 contact 分发、edge）；按键、Wi-Fi、GPU、RTC 未通；0131b 有 USB probe，但未形成可用接口。
- 启动前镜像 hash 固定；启动后的 live-root/ring/日志 hash 和时序易变（见
  `GUARANTEE.zh.md` 的「hash 稳定性」）。

## 验证

```sh
python scripts/verify-local.py
python tools/image/boot_verify.py <boot.img> <base.img>
```

`boot_verify.py` 打印镜像 SHA、page/kernel、SWEETXNU 字段、ADT SHA 和
cmdline；可选的 base 对比检查 kernel 槽之外的尾部。

## 恢复

见 [`08-recovery.md`](08-recovery.md)。每次刷前保留完整恢复镜像；没有
recovery 分区，也不能 `fastboot boot`。
