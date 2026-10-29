# 可复现性保证

[English](GUARANTEE.md) · **中文**

**状态 2026-10-22 —— 有单台设备证据的文档化配方。**
B+NOP 首启 -> A'、CI kernel 启动和 0085 真实触摸启动已在作者设备上观察到。
这不是已经独立复现的第二台/干净室保证；更详细的测试保证暂缓。

**范围说明（2026-10-29）：** 本文只覆盖历史 0085/0084 成功包；2026-10-29
主线使用 `config/0140.env` 与 `config/0131b.env` 的 pin，见
`docs/zh/11-ci-baseline.md`。

## 范围

只覆盖成功路径：

```
stock LK -> XNU 8796 -> iOS 16.7.16 用户态
  -> 锁屏 -> 真实底边上滑（0085）-> SpringBoard 桌面
  或 -> 合成上滑（0084）-> SpringBoard 桌面
```

失败路线是历史证据，不在保证范围内。

## 定义

同时满足以下条件时：

- 同一设备情况（ruby / MT6877，Android 12 / MIUI 13.0.4，已解锁，slot
  `_a`，分区布局见 `docs/zh/device.md`）；
- 同一 boot 镜像和 iOS root/ICL 状态（见下方 hash）；
- 启动参数为 `config/0085-boot.cmdline`（合成上滑镜像用
  `config/0084-boot.cmdline`）；
- 按 `docs/zh/09-reproduce.md` 和 `docs/zh/05-userland.md` 的步骤操作；

则**预期**能复现成功状态。2026-10-22 在作者一台设备上做过验证；没有做
第二台设备或干净室验证。

任何一项 hash 不同，本保证不适用；那是一个不同的配置。

## 成功状态 bundle

| 项 | 值 | 说明 |
|---|---|---|
| 基线 | `MakrSas/ios-topaz@5095ac1` | 上游 commit |
| Patchset（0085） | `cf4008e3...` | 88 个文件；与 harness 构建一致 |
| Patchset（0084） | `de1824c2...` | 87 个文件；上一里程碑 |
| 0010/0012 改动 | `1edb6633...` | 小的基线补丁 |
| 真实触摸内核 | `9eb9acac...` | 0085；exec-data `e4823afb...` |
| 真实触摸镜像 | `ace60d16...` | 外部；不在仓库 |
| 原始内核（0084） | `b38fca5f...` | 上一里程碑实际启动 |
| CI 重建内核（0084） | `8a80855d...` | run `39648068844`；已启动；payload 工具 ref `33852e3` |
| boot 镜像（0084） | `94c639d1...` | 外部；不在仓库 |
| root 镜像（A） | `e698339d...` | 外部；成功快照；用前复核 |
| ICL 原块 | `ae317804...` | 还原路径 |
| ICL 补丁块 | `4a489542...` | 绕过 |
| 启动参数 | `config/0085-boot.cmdline` | 真实触摸 cmdline；0084 为上一里程碑 |
| 成功判据 | 所有计时从 Apple logo 起：首次启动约 60 秒（实测 58 秒）；热重启约 22 秒；2026-10-22 B+NOP 首启 22 秒 / 30 秒；上滑到桌面；动画正常 | 作者 boot22/boot23 和 2026-10-22 run |

root 状态（全部为外部工件；完整镜像不在仓库）：

| 状态 | SHA-256 | 含义 |
|---|---|---|
| A 成功快照 | `e698339d...` | boot22 之后；ICL NOP + 首启状态 |
| B 首启前 | `985c30...` | pulled+seeded；ICL 原块；boot22 diff 把 B -> A |
| C clean 基础 | `34c2882d...` | mkiosroot + tweaks；还需要首启/seed |
| A' 首启快照 | `55e2ab2c...` | 一次 B+NOP 首启的快照；新的首启会不同 |

success bundle 是 A。旧 pin 写的是 B；2026-10-22 只读 root 审计后修正。
A' 是首启快照，不是稳定 pin；启动后的 hash 是易变的。

完整 hash：

```text
patch85    cf4008e309cfa566e3df968592a2d3f3224a9b3d0813d6054326115fecc0a03f
kernel85   9eb9acac8a4c936c1861fba1e0d29c105b714e8d0e6d407b48f4237076e6b947
execdata85 e4823afb97360e24708184d09c0dc6c9f7280e33d5c4aefbeb901b3fa9b11e3e
image85    ace60d1645ec271cdbd55b7007456cb578168ca708382aafae8fbf506e68f6c8
payload85  dbc57e96396f2e3e23213a76d300b1a329e2b4a320bc7363cf99ce0fc9e52b1c
ci85 kern  904e10dfc14c5e9cc0abd8a6ad7a8b6399526e31a33deb64ceb93cdde0a30d12
ci85 image 54d1b3066a3782cab36135dbe8d666cf53bbd6837b8394105d7e61de9b32b10d
patch84    de1824c28b5e56f7c60988c33501cd5bbfd24a4159d9358223fd2af11392d360
0010/0012  1edb66332bb4daa8b1abcd6c4de77a0e88ed9c7e9bb4a2a7045a2696e53ab338
kernel84   b38fca5f38cfb721e21228eac4dd4b355000d1b850bdf204afba9ff8b8d1afcd
ci kernel  3ceb9b3490f8c8ecaa74348c3c5cb02d7302d0ec7f87006fe8354e9d2011a831
ci kernel2 8a80855d1f615cf72f6ebb9f6213d0d55c8f799ad80286f0aab9f80d3215f38a
ci payload 2749bf1cf398f750d25ed6e84bbb529d5cc5ba3e1ef6be464bff09d0ec87a053
ci image   87dd4910247cf746df281e77cdf8d63528a148757a82e2b97be58ee5d9183162
boot84     94c639d1f45197718c62bd09c32c72b39710ba23de60f4a04bba96014bce1cb6
root A     e698339d0e228609c2d98f16ae8dd44a5149f2ccc19a44b98d5d08845c53f96f
root B     985c30fcca28cb79e6ad6d30a1ff4b4b6b7306b69d6e480cd7cccf4fb5ca11e3
root C     34c2882d3b722e53c9755dad3b74284d6ebba6f00256838d407ba3694b1a456d
root A'    55e2ab2c6e5494f473ece06a1c2bed728ed528bb257b67f01413d1aa51c76f11
icl orig   ae3178046fe7cb9e08291c39dc4773429be26c35472c6fbd9135d5f2a225fd73
icl pat    4a4895422dcec766b90b65c067ecb06ef8fd3e346c03ee7e2464a85f62a73b74
```

root 和 boot 镜像**不在仓库**：它们含不可分发的 Apple/Android 材料。hash
就是契约。

设备基线 hash（GPT/boot/vbmeta）有意**不发布**，因为可能成为设备指纹；
设备情况写在 `docs/zh/device.md`。上表的工件 hash 才是契约。

## hash 稳定性

固定 / 启动前（身份）：0085 patchset `cf4008e3...`、0084 patchset
`de1824c2...`、启动参数、ICL 块、命名的 root 快照（A/B/C/A'），以及某次
run 的 kernel/payload/image 工件。CI 构建不是位级一致；patchset hash 是
源码门禁，Mach-O exec-data hash 是工件门禁（0085 参考 `e4823afb...`）；
记录该 run 的实际完整 artifact hash。A' 是一次首启快照；新的首启会是一个
新状态。

易变 / 启动后（不要求相同）：任何启动后的 live root（A' -> A''）、
UUID/时间戳、日志/缓存、SWEETLOG ring 及其解码文本、UI 像素/时序。契约是
启动前身份 + 行为（锁屏、autoswipe、桌面、ring 标记），不是启动后的整盘
hash。

## 保证

- Patchset 和 recipe：workflow 只有在 recipe 还原出 `cf4008e3...`（88 个
  文件）时才编译；0085 首次 CI run `39694456200` 已成功，exec-data 与实机
  内核一致。
- 离线工具：host 检查、合成与真实 ICL 块往返。
- 成功路径的文档化步骤和范围。
- 2026-10-22 的单台设备证据（B+NOP 首启 -> A'、CI kernel 启动），作为
  记录证据；它不是第二台设备的保证。
- 失败路线的历史证据，明确标注不支持。

## 重建

`scripts/build-payload.sh` + `tools/image/pack_boot.py` 使用上面的输入和 seed
`0x84` 产出 `a0ce0fe1...`。重建镜像与原件**布局等价，但不是字节一致**：
原镜像用了 `os.urandom` filler。重建镜像用 `tools/image/boot_layout.py`
对比；成功镜像仍是 `94c639d1...`。

## 不保证

- 另一台设备上的独立启动。
- 精确 UI 像素、时序或应用状态。
- 不同的 CI 构建/payload，或 CI 重建内核在第二台设备上的启动。2026-10-22
  的 run 在作者设备上用 payload ref `33852e3` 启动成功；严格 pin 重打仍未做。
- 启动后的 live-root/ring/日志 hash、跨首启的 A'、UI 时序。
- 外部 root builder 和 shim/ADT builder 作为干净室工具。
- 原始（未打补丁）ICL 块的回归。
- root/boot 工件本身（不在仓库）。
- 原 boot 镜像的字节级重建（原 filler 是随机的）。
- 任何失败路线的设备行为。

## 暂缓的验证

因时间和精力暂缓，不是因为已知失败：

- 第二台设备启动测试；
- Linux 干净室 host CI；
- 严格 pin 的 payload 重建（2026-10-22 的测试用了 ref `33852e3`）；
- root builder 和 shim/ADT builder 作为干净室工具；
- 原始 ICL 块回归；
- 按键和 USB；
- 长时间稳定性；
- 第二台/干净室设备回归；单台首启和 CI kernel 已在 2026-10-22 跑过。

设备基线 hash（GPT、boot_a/b、vbmeta）有意不发布；设备情况写在
`docs/zh/device.md`。

这些是明确的未完成项。本文件记录单台设备证据和文档化配方；它还不是
第二台设备的保证。

## 使用方式

1. 先把自己的设备情况和工件 hash 与上表对比。
2. 按 `docs/zh/09-reproduce.md` 和 `docs/zh/05-userland.md` 操作。
3. 任何 hash 不同就停止：那是不同配置，不是本保证覆盖的复现。
4. 如果做了独立复现，记录 hash 和结果（脱敏），并更新本文件。

## 失败路线

`patches/historical/0081-0083` 和 `docs/zh/07-experiments.md` 的失败目录是
证据。它们**不属于**成功构建，没有做设备重测，也不在保证范围内。
