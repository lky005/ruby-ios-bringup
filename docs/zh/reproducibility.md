# 可复现性（理论）

[English](../en/reproducibility.md) · **中文**

仓库按 **Tier B** 发布成功路径：只放自己的补丁、工具和文档；上游树由 recipe
拉取，不复制进仓库；不公开完整 delta，也不放 Apple/Android 二进制。保证是文档级、
理论级的，不是已经独立复现的设备保证。

**2026-10-29 基线来源：** 0001–0079 的 82 个文件由 CI 从私有内容寻址镜像拉取，
公开 pin 是清单根 `829d7598…`（82 文件，LF 归一化），不是仓库地址；仓库/ref/只读
deploy key 存在 Actions secrets（`BASELINE_REPO`/`BASELINE_REF`/`BASELINE_SSH_KEY`）。
外部复现可用公开上游回退：`ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh`，
同一条清单根校验。

main（2026-10-29 集成，由 `merge-ramdisk-usb-2026-10-29` 压缩）构建 ramdisk 集（`27894e7b…`，
137 文件）；`usb-0131b-probe-write` 分支构建 `29449e32…`（135 文件），
配置在 `config/0131b.env`。两条线共用同一 82 文件基线与私有镜像凭据。

## 公开什么

- `patches/`：0080 UFS、0084 autoswipe、历史 0081-0083。
- `ci/prepare-baseline.sh`：从私有镜像（或显式公开回退）取固定基线、校验
  清单根、加本项目补丁、应用 0010/0012 小改动。
- `ci/baseline_manifest.py`：82 文件基线清单根校验（LF 归一化）。
- `ci/patchset_hash.py`：patchset 规范哈希（主线 0140：137 文件；
  USB 分支 0131b：135 文件）。
- `ci/baseline-changes.patch`：只含 0010/0012 小改动。
- `tools/image/`、`tools/twrp/`、`scripts/check-bundle.py`：离线检查。
- `scripts/build-payload.sh`、`tools/image/pack_boot.py`、
  `tools/image/boot_layout.py`、`scripts/test-pipeline.sh`：host 管线。
- `config/0086.env`：USB P0 构建/测试 cmdline；`config/0085.env` 保留 0085
  工件 hash 和 boot cmdline（`0084.env` 为上一里程碑）。

## 不公开什么

- `ci/ruby-baseline.diff` 或任何完整上游 delta（已从历史移除）。
- Apple 固件、iOS root、dyld 共享缓存。
- stock/Magisk/TWRP boot 镜像。
- 设备基线 hash（GPT/boot/vbmeta）；见 `device.md`。
- 全量日志、设备 dump、diff 数据、媒体（稍后）。

## 防漂移

| 控制 | 防止什么 |
|---|---|
| 基线清单根 `829d7598…` + 上游 `5095ac1` | 基线内容漂移或上游分支移动 |
| 私有镜像 ref（Actions secret） | 镜像被改；清单根不匹配即停 |
| 固定 topaz 删除清单 | 公开回退路径的补丁残留 |
| recipe 失败即停 | 文件缺失或 0010/0012 上下文变化 |
| LF 归一化 | Windows/macOS 换行漂移 |
| `PATCHSET_SHA256`（按分支） | patchset 内容变化；集成 `27894e7b…`，USB `29449e32…` |
| `ci/baseline-changes.patch` SHA | 基线改动漂移 |
| `check-bundle.py` | kernel/boot/root/ICL/cmdline 不对 |
| Actions 按 SHA 固定 | CI 供应链漂移 |
| `permissions: contents: read` | CI token 权限过大 |
| Xcode 15.0.1 固定 | 工具链漂移 |
| 干净 git 历史 | 旧 delta 被带进公开历史 |

## Host 管线状态

host 阶段已具备并用 0084 输入测过：payload `50701e81…`、确定性重建
`a0ce0fe1…`、布局对比 golden PASS（没有 golden 时用 config pin 也 PASS）；
只有 filler 字节不同。Linux host CI 在最终 docs/template-only 改动前已绿；
见 Actions（`verify-local` 和 TWRP 交叉编译在 Ubuntu 上通过）。shim/ADT 仍是外部
输入，不碰 16 GiB root。原镜像的字节级重建不可能，因为 filler 是随机的。

## 仍可能坏的地方

- 私有镜像不可达或 deploy key 失效；用本地 bundle/副本恢复，或显式走公开回退。
- `macos-14` runner 或 Xcode 15.0.1 消失；workflow 会明确失败。
- Homebrew 版本变化；记录但不固定。
- root/boot 工件丢失或被替换。
- 设备固件/GPT/面板与 `device.md` 不一致。
- ICL 偏移是版本相关的；换 root 就不匹配。
- 原 boot 镜像的字节级重建；原 filler 是随机的。

## 测试状态

这次打包没有做设备回归测试。进桌面是历史结果（boot23）；CI 只构建内核。
精确设备效果依赖同一 root/boot 工件和同一类设备。见
[`../../GUARANTEE.zh.md`](../../GUARANTEE.zh.md)。
