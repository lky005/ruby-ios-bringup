# 11 — CI 基线与分支 pin

[English](../en/11-ci-baseline.md) · **中文**

> 状态标签沿用[仓库 README](../../README.zh.md)：**[measured]**、
> **[inferred]**、**[historical]**。没有来源的数字就是 bug。

内核 CI 不再依赖一个活着会变的上游仓库。它由 Apple 的 xnu tag、一个内容
固定（content-addressed）的 82 文件基线，以及本项目的增量拼装。

## 基线 [measured]

- 82 个文件：79 个 `.patch` + 3 个 staging `.sh`（sweet 0001-0079）。
- 清单根 `829d7598...`（对 LF 归一化后的文件计算）；`MANIFEST.sha256`
  逐文件列出。公开 pin 是清单根，不是仓库地址。
- CI 从私有内容寻址镜像取这组文件。仓库、ref 和只读 deploy key 保存在
  Actions secrets（`BASELINE_REPO`、`BASELINE_REF`、`BASELINE_SSH_KEY`）；
  不公开镜像 URL 或密钥。
- Apple 源码：`apple-oss-distributions/xnu` tag `xnu-8796.141.3`
  （`f625db25...`），由构建框架克隆。

## 分支与 pin [measured]

| 线 | patchset | 文件数 | 配置 | 内核参考 |
|---|---|---|---|---|
| main（2026-10-30 集成） | `f47f4c19...` | 139 | `config/0143.env` | full `d2eae74d...`，exec `6fa65088...`（CI `41022192026`） |
| main（2026-10-29 集成） | `27894e7b...` | 137 | `config/0140.env` | full `3acefe47...`，exec `721e5daf...` |
| USB 0142 / 0143 分支 | `d0c5ab5e...` / `f47f4c19...` | 138 / 139 | `config/0142.env`、`config/0143.env` | CI `41015790742` / `41022192026` |
| USB（`usb-0131b-probe-write`，历史） | `29449e32...` | 135 | `config/0131b.env` | full `4e945ce6...`，exec `06db2bb3...` |

- main 包含 0080/0084/0085、0086-0131b、0140/0141、0142 和 0143。
- 0142 把 EP2 IN bulk MPS 扩到 512；0143 把每帧日志扩到 511 B（16 B 头
  + 最多 495 B 文本），并在停 QMU 后 reset TX 环。host 侧首会话 XACT
  在 0143 仍未闭环。
- 0131b 分支保留自己的 workflow 和 patch 列表；main 保留
  `config/0131b.env` 与 `config/0131b-boot.cmdline` 作为历史。
- 内核 run `41022192026` 构建 0143，exec-data 与 `6fa65088...` 一致；
  `41015790742` 对应 0142（`99d98d80...`）。2026-10-29 的
  `40822689195` / `40824668335` 作为历史 main/USB 参考保留。
- 2026-10-30 行是 0143 合并候选；在压缩提交合并前，`main` 仍指向
  2026-10-29 行。
- 重新构建的内核 full SHA 会在 `__TEXT` 元数据和压缩的 `__CTF` 段上与参考
  不同；所有代码/数据段与 `__LINKEDIT` 一致。exec-data 才是门禁。

## Recipe

1. 取 82 文件基线（私有镜像，或公开回退
   `ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>`），做 LF
   归一化并校验清单根。
2. 加入本分支补丁，应用 0010/0012 改动，归一化并校验 patchset 哈希。
3. 用 `blacktop/darwin-xnu-build` 在 `macos-14` + Xcode 15.0.1 上构建。
4. 校验内核 exec-data 哈希。

## 本地检查

```sh
BASELINE_DIR=<baseline> sh ci/prepare-baseline.sh <dest>
# 公开回退
ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>
python ci/baseline_manifest.py --patches <dest>/xnu/patches \
  --expect-root <manifest-root> --expect-count 82
python ci/patchset_hash.py <dest>/xnu/patches
python scripts/verify-local.py --ci-config config/0140.env
```

USB 分支使用 `--ci-config config/0131b.env`。

## 边界

- 私有镜像 URL、deploy key 和基线代码不公开。
- Apple 固件、iOS root、共享缓存和 boot 镜像不公开。
- 上游项目在 pin 上没有 LICENSE；镜像保持私有。完整基线不再分发；只发布
  清单根与已披露的 `ci/baseline-changes.patch`（0010/0012 改动）。
- 外部用户可以使用公开上游回退；清单根校验的是同一份内容。
