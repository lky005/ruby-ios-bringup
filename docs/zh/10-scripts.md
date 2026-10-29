# 10 — 脚本说明

[English](../en/10-scripts.md) · **中文**

每个入库脚本都写清用途、边界和失败模式。“为什么存在”比“怎么运行”更重要：
这些工具大多是因为更简单的路会静默失败才出现的。

## 清单

| 脚本 | 用途 | 风险 | 验证 |
|---|---|---|---|
| `tools/image/icl_nop.py` | 在 raw 块/镜像上改 4 字节 | 离线写，默认 dry-run | 真实块往返 |
| `tools/image/dyld_scan.py` | 在 split dyld cache 里定位 VA | 只读 | MG 工作中使用 |
| `tools/image/boot_verify.py` | 检查打包 boot 镜像 | 只读 | 0084/0085 镜像 |
| `tools/twrp/blkdiff.c` | 与 4K CRC 图对比 | 对镜像是只读 | 多轮启动 |
| `tools/twrp/blkpatch.c` | 按索引写 diff 块 | **raw 设备写** | 多轮启动 |
| `tools/twrp/twrp-guard.sh` | 非 TWRP 拒绝运行 | 门禁 | 主机拒绝 |
| `tools/twrp/build.sh` | 交叉编译两个静态工具 | 主机构建 | 构建配方 |
| `src/bringup/build_full_a.py` | 把 payload 打进 boot 槽 | 离线写 | 红屏/探针镜像 |
| `src/bringup/build_shim_full.py` | 同上，针对 stage shim | 离线写 | 探针镜像 |
| `src/bringup/mkboot_v2.py` | 生成小 Android boot 镜像 | 离线写 | 早期 bring-up |
| `src/bringup/repack_stock.py` | 用 payload 重打 stock 镜像 | 离线写 | 早期 bring-up |
| `src/ufs-probe/build_ufs_full.py` | 打包 UFS 探针 | 离线写 | UFS 探针镜像 |
| `scripts/fetch-base.sh` | 拉固定基线供检查 | 只读/网络 | 可选 |
| `scripts/verify-local.py` | 主机检查 | 只读 | 本地通过 |
| `scripts/check-bundle.py` | 刷前核对工件 hash | 只读 | 由 config 驱动 |
| `.github/workflows/xnu.yml` | 构建当前内核 | CI 构建 | recipe + patchset 哈希 |
| `ci/prepare-baseline.sh` | 取基线、校验清单根、加补丁、校验哈希 | 网络 + 临时写 | 本地已测 |
| `ci/patchset_hash.py` | patchset 规范哈希（集成：137 文件；USB：135） | 只读 | 与 recipe 一致 |
| `ci/baseline-changes.patch` | 0010/0012 小改动 | 数据 | 哈希固定 |
| `scripts/build-payload.sh` | 从 kernel+ADT+cmdline 生成 payload | 网络 + 离线写 | 已测 |
| `tools/image/pack_boot.py` | 确定性 128 MiB boot 镜像 | 离线写 | 已测 |
| `tools/image/boot_layout.py` | 重建镜像 vs golden 布局对比 | 只读 | 已测 |
| `scripts/test-pipeline.sh` | payload → pack → layout（0084 里程碑） | 临时写 | 0084 通过；0085 用 `09-reproduce` 的三条命令 |
| `config/0140.env`、`config/0131b.env` | 当前分支 pin 与 boot cmdline；0086 文件为历史 | 数据 | run/pin 检查 |
| `config/0085.env`、`0085-boot.cmdline` | 来源记录（真实触摸） | 数据 | run/pin 检查 |
| `config/0084.env`、`0084-boot.cmdline` | 上一里程碑（合成上滑） | 数据 | 历史 |

## `tools/image/icl_nop.py`

**初衷：** 内核通知已送达，卡住的是用户态 MG 调用；最小可回滚的绕过是
4 字节 `nop`。16 GB 镜像不能盲改，所以需要 SHA 校验和备份。

- **输入：** 4K 块，或 raw 镜像 + 块号。
- **输出：** 补丁块/镜像；镜像模式留备份。
- **不做：** 不找偏移、不证明语义、不刷机。
- **风险：** 离线写；默认 dry-run。
- **失败模式：** 块号/偏移错 → 原字节不匹配；备份已存在 → 不加 `--force`
  就拒绝；镜像已挂载 → 不要用。
- **示例：**

```sh
python tools/image/icl_nop.py --image <root.img> --block-index 2438140 \
  --in-block-offset 0xF0C --expect-block-sha <orig> \
  --expect-patched-sha <patched> --apply
```

## `tools/twrp/blkdiff.c` / `blkpatch.c`

**初衷：** 16 GiB `adb pull` 分块也会卡；`blkdiff` 在手机端算 CRC32，只写
变化的 4K 块；`blkpatch` 按索引写回。16 GiB 扫描约 45 秒。

- **输入：** 镜像/分区、CRC 图、diff/idx、块数。
- **不做：** 不备份、不检查挂载、不自己检测 TWRP。
- **风险：** `blkpatch` 写 raw 块；必须通过 `twrp-guard.sh`。
- **失败模式：** 短读、块数错、设备错、文件系统已挂载、忘记 `sync`。
- **示例：**

```sh
sh tools/twrp/twrp-guard.sh ./blkdiff /dev/block/by-name/iosroot \
  crc.bin diff.bin diff.idx 16384
```

## `tools/image/dyld_scan.py`

**初衷：** `InstalledContentLibrary` 在 26 个 split-cache 文件之一；猜偏移
很浪费启动次数。这个工具解析主缓存和子缓存，打印所属 image、文件偏移和
前 0x80 字节。

- **风险：** 只读。
- **不做：** 不提取、不打补丁、不修改。
- **示例：**

```sh
python tools/image/dyld_scan.py --cache-dir <dyld-dir> \
  --image-name InstalledContentLibrary --va 0x1b11b9f0c
```

## `tools/image/boot_verify.py`

**初衷：** 128 MiB 布局很容易在细节上弄错（kernel 槽、DTB、AVB footer）；
刷前先验 payload 字段。

- **风险：** 只读。
- **检查：** 镜像 SHA、page/kernel、SWEETXNU 头、ADT SHA、cmdline、可选
  尾部对比。
- **不做：** 不验签名/AVB、不刷机。

## `src/bringup/build_full_a.py` / `build_shim_full.py`

**初衷：** LK 要求 stock kernel 流大小；打包器用 gzip FEXTRA 补齐保持槽
大小，DTB/ramdisk/AVB 位置不变。

- **输入：** base 镜像、payload、输出。
- **不做：** 不签 AVB、不刷机、不检查设备。
- **失败模式：** payload 太大装不进槽；payload 偏移错；非 ARM64 payload。
- **示例：**

```sh
python src/bringup/build_full_a.py --base <stock.img> \
  --payload <payload.bin> --out <out.img>
```

## `src/ufs-probe/build_ufs_full.py`

**初衷：** 把 UFS 只读探针装进同样保持大小的槽；filler 用固定种子，
重复构建结果一致。

- **不做：** 不写 UFS、不刷机。
- **示例：**

```sh
python src/ufs-probe/build_ufs_full.py --base <stock.img> \
  --shim <Image> --out <probe.img>
```

## `ci/prepare-baseline.sh` + `.github/workflows/xnu.yml`

**初衷：** 上游没有 LICENSE，不能把上游树复制进仓库，也不公开完整 delta。
recipe 取内容固定的 82 文件基线（私有镜像，或 `ALLOW_PUBLIC_UPSTREAM=1`
回退）、校验清单根、加入本项目补丁、应用 0010/0012 小改动、统一 LF，并在
构建前校验 patchset 哈希（主线 137 文件；USB 分支 135 文件）。

- **不做：** 不刷机、不打包镜像、不跟随移动分支、不公开完整上游 delta。
- **失败模式：** 基线清单根不匹配 → 停止；0010/0012 上下文不匹配 →
  `git apply` 失败；patchset 不匹配 → 编译前停止。
- **pin：** 见 `config/0140.env`、`config/0131b.env` 和 `ci/README.md`。

## `scripts/build-payload.sh`

**初衷：** 0084 payload 是确定性的；0085 镜像使用随机 filler，按布局校验。
payload 工具在上游，ADT 是外部输入。
wrapper 按固定 commit 拉上游工具，用用户的 kernel/ADT/cmdline 跑
`mkpayload.py`，并校验 payload SHA。shim/ADT 不入库。

- **输入：** kernel、ADT、cmdline 文件、输出。
- **不做：** 不拉 kernel/ADT、不打包 boot、不刷机。
- **失败模式：** 输入缺失、基线不匹配、payload SHA 不匹配。
- **已验证：** 0084 输入产出 `50701e81…`。

## `tools/image/pack_boot.py`

**初衷：** 原打包器用 `os.urandom`，镜像 SHA 不稳定。新打包器用固定 seed
的 SHA-256 filler、保持 kernel 槽大小（FEXTRA）、校验 shim/payload 范围和
tail。

- **输入：** base 镜像、shim、payload、输出。
- **不做：** 不生成 payload、不刷机、不改 base tail。
- **失败模式：** shim/payload 太大、gzip 装不下、回读不一致。
- **已验证：** seed `0x84` 两次运行输出相同 `a0ce0fe1…`；布局与 0084
  golden 一致。
- **说明：** 原 `94c639d1…` 的 filler 是随机的，不能按字节重建。

## `tools/image/boot_layout.py`

**初衷：** 重建镜像的 SHA 按设计会不同；这里只比较有意义的布局：SWEETXNU
字段、ADT、cmdline、shim 范围、payload 范围和 tail。

- **风险：** 只读。
- **不做：** 不刷机、不修改、不需要 root。
- **已验证：** 重建 vs 0084 golden 全部 PASS；只有镜像字节不同。
- **无 golden：** 传 `--config config/0085.env`，改用 pin 的 header/ADT/
  cmdline/shim/payload 值校验。

## `scripts/test-pipeline.sh`

**初衷：** 一条 host-only 命令跑 payload → pack → layout，使用外部输入和
<1 GiB 工件，不碰 16 GiB root。

- **不做：** 不碰设备、不刷机、不改输入。
- **示例：** 见 `scripts/README.md`。

## `scripts/check-bundle.py`

**初衷：** 刷前把 kernel、boot、root、ICL 块和 cmdline 与成功 bundle 对比；
任何不符都是不同配置，不在保证范围内。

- **风险：** 只读。
- **不做：** 不碰设备、不改镜像。
- **示例：**

```sh
python scripts/check-bundle.py --kernel <kernel> --boot <boot.img> \
  --root <root.img> --icl-orig <orig.bin> --icl-patched <patched.bin> \
  --cmdline <cmdline.txt>
```

## `scripts/verify-local.py` + `tools/twrp/twrp-guard.sh`

**初衷：** 在主机上抓语法、PII、patchset 漂移和 ICL 往返错误；raw block
工具在非 TWRP 环境直接拒绝。

- **风险：** 只读；ICL 测试只写临时目录。
- **不做：** 不碰设备、不刷机、不改镜像。
- **示例：**

```sh
python scripts/verify-local.py
sh tools/twrp/twrp-guard.sh ./blkdiff ...
```

## 为什么不是别的方案

| 选择 | 替代 | 为什么不用 |
|---|---|---|
| ICL NOP | 继续加内核 stub | 内核送达已 `sent=1`，墙在消费者 |
| 内核合成上滑 | 用户态注入 | 没有 shell/日志工具；要签名/entitlement |
| `blkdiff`/`blkpatch` | `adb pull` 16 GiB | 长连接会卡；只搬 244 MiB diff 可行 |
| 固定基线 + recipe | 把上游树复制进仓库 | 上游无 LICENSE；patchset 哈希保证一致 |
| `boot_verify` | 刷了再看 | 128 MiB 布局错了 LK 会静默失败 |
| 重建用 `boot_layout` | 对比镜像 SHA | 原 filler 是随机的；布局才是可复现门禁 |
