# 文档（中文）

[English](../en/README.md) · **中文**

证据优先。每条结论标注 **[实测]**、**[DTS]**、**[推断]** 或 **[历史]**；
未验证的内容不会写成事实。文档不含个人路径、设备标识或 Apple 二进制。

## 阅读路径

| 时间 | 读什么 | 目标 |
|---|---|---|
| 5 分钟 | `../../README.zh.md`、`../../STATUS.md` | 哪些通了、哪些没通 |
| 30 分钟 | `08-recovery`、`09-reproduce`、`10-scripts` | 构建、刷写、恢复 |
| 深入 | `01`–`07` | 机制、证据、走过的弯路 |

## 章节

| 文档 | 内容 |
|---|---|
| [`01-architecture`](01-architecture.md) | 启动链与组件地图 |
| [`02-hardware`](02-hardware.md) | 实测 MT6877 硬件坐标 |
| [`03-boot-chain`](03-boot-chain.md) | LK、128 MiB 镜像、看门狗/console |
| [`04-display`](04-display.md) | surface 到 panel、缓存维护 |
| [`05-userland`](05-userland.md) | launchd/LS/MG 死锁、ICL NOP 反汇编 |
| [`06-input`](06-input.md) | 真实 Goodix 触摸、SweetHID、边缘位、合成上滑 |
| [`touch-goodix-9916r`](touch-goodix-9916r.md) | GT9916R 硬件、上电/协议手册、bring-up 记录 |
| [`07-experiments`](07-experiments.md) | 时间线、失败目录、决策记录 |
| [`08-recovery`](08-recovery.md) | Android 恢复、TWRP、raw I/O |
| [`09-reproduce`](09-reproduce.md) | 构建、打包、刷写、验证 |
| [`10-scripts`](10-scripts.md) | 逐脚本用途与边界 |
| [`11-ci-baseline`](11-ci-baseline.md) | 内容固定的基线、分支 pin、exec-data 门禁 |
| [`appendix-dualboot`](appendix-dualboot.md) | 可选布局；仅方法说明 |
| [`glossary`](glossary.md) | 代号、缩写与状态标签 |
| [`device`](device.md) | 设备情况；不发布基线 hash |
| [`root-recipe`](root-recipe.md) | root 输入与步骤；不含 root 镜像 |
| [`reproducibility`](reproducibility.md) | Tier B recipe、防漂移、暂缓测试 |
| [`保证`](../../GUARANTEE.zh.md) | 成功路径范围、bundle hash、暂缓测试 |

## 规则

- 没有来源的数字视为 bug；引用 live FDT、日志行、SHA 或可重跑的命令。
- 标注 [实测]/[推断]/[历史]，不把猜测写成事实。
- 命令用占位符（`<base>`、`<out>`、`<workdir>`），不写个人路径。
- 不放 Apple 固件、iOS root、共享缓存、设备 dump、序列号、IMEI/MAC 或账号。
- 每个脚本必须写“不做什么”和失败时如何安全退出。
