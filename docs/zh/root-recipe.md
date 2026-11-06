# Root recipe

[English](../en/root-recipe.md) · **中文**

仓库不含 root 镜像。成功 root（A）是 **pulled v14 root** + boot22 首启状态 +
ICL 块补丁，工件 hash 是 `e698339d...`。首启前的 pulled+seeded root（B）是
`985c30...`；clean mkiosroot 基础（C）是 `34c2882d...`。boot22 diff（62,490
个 4K 块，外部）把 B -> A。这一页是 recipe，不是安装器，也不自动化 16 GiB
root。

## root 是什么

- iPhone X iOS 16.7.16（20H392）用户态的 HFS+ 镜像。
- A：boot22 之后成功快照，含 ICL NOP 和首启状态。
- B：boot22 之前 pulled+seeded root，含 ICL 原块；boot22 diff 把 B -> A。
- C：clean mkiosroot + tweaks 基础；C 单独启动可能停在 LS/MG，还需要设备
  首启/seed。
- A'：从 B+NOP 首启得到的快照；一次 run，不同首启会不同。新的首启是新状态
  （A''）。
- v14 谱系：pulled `/private/var` + fsck + `DataMigration.plist`
  （`LastSystemVersion=20H392`）加传输 tweaks。
- boot22 diff：62,490 个 4K 块（244 MiB），包含首启状态；diff 数据不在仓库。
- ICL 4K 块：`2438140`，原块 `ae317804...`，补丁块 `4a489542...`。
- 精确状态很重要。fresh IPSW root 是另一条路，可能在 UI 前停在
  LaunchServices/MobileGestalt。

## 输入

- iPhone X iOS 16.7.16（20H392）IPSW 和 HFS+ 镜像工具。
- pulled root（优先）或 fresh IPSW root + 一次设备首启。
- 精确的 v14 tweaks：Setup skip、`BKNoWatchdogs`、`HAL.disabled`、
  移除 CommCenter、`data_ark`、ByHost 迁移偏好、容器、MediaToolbox
  recorder off。
- TWRP A12 和一份已知可启动的 `boot_a`。

## 步骤概要

1. 解出 D22AP IPSW；建 16 GiB HFS+ 镜像（双系统示例里是 17 GiB
   `iosroot`；默认路径可用专用分区）。
2. 复制用户态；应用 v14 tweaks，seed 容器/ByHost/`data_ark`。
3. 在设备上首启，生成首启状态；冻结 root 镜像。成功状态从 B + ICL NOP
   出发；得到的 A' 不要求 hash 等于 A。这一步在设备侧，不在本仓库自动化。
4. 用 `tools/image/icl_nop.py` 打 ICL 4K 块；核对原块/补丁块 hash。
5. 用 TWRP raw `dd` 把冻结 root 写到 `iosroot`；核对 SHA。
6. 保留原 root 镜像和 ICL 原块用于回滚。

## 限制

- 仓库不含 16 GiB root 或 diff 数据。
- A/B/C 都是外部状态。B 和 C 的完整镜像不保留；A 是成功快照；A' 是首启
  快照。
- root 镜像不可分发；使用者自备。
- 启动前镜像 hash 固定；启动后的 live-root/ring/日志 hash 易变。见
  `docs/records/GUARANTEE.zh.md` 的「hash 稳定性」。
- 精确首启状态可能需要一次设备运行；纯 host recipe 无法重建 pulled 手机
  状态。
- 这次打包没有做设备回归测试。
