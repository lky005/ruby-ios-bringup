# 05 — 用户态：LS/MG 与 ICL NOP

[English](../en/05-userland.md) · **中文**

锁屏这堵墙看起来像内核通知 bug，其实不是：内核已经送达
`IOServiceMatched`，卡住的是用户态 MobileGestalt 消费者的 runloop/semaphore。
ICL 的 4 字节 NOP 绕过的是这个消费者。

## 症状

```
lsd t0: _LSServerCleanEphemeralMobileContainersForFirstBoot
        -> performJournalRecovery -> dispatch_sync

lsd t1: dispatch_semaphore_wait_slow
        <- MGIOKitSupport helper
        <- libMobileGestalt
        <- MIInstallationIdentity
        <- InstalledContentLibrary __GenerateBuiltInAppInstallSessionID
```

SpringBoard t0 等 `_LSContextInitCommon`，t1 持锁等 lsd；lsd 两条线程经 MG
路径互等。

## 已排除

| 假设 | 实验 | 结果 |
|---|---|---|
| CPU 数/A78 | `cpus=6` + 上游 cache | 栈与 `cpus=8` 逐字节相同 |
| launchd cache 变体 | 上游 vs boot-forced | 不变 |
| ADT 缺 Wi-Fi 节点 | 加 `/arm-io/marconi-wifi` | 匹配 `IOPlatformDevice`，但仍无 `IONetworkController` 通知 |
| 缺 IONetworkController 服务 | 内核 0082 stub | stub 发布成功；该次启动通知送达 0 次 |
| semaphore 超时 | `mov x1,#-1` → `#0` | lsd 离开等待但 crash-loop（`ns 2 code 0xa`） |
| 需要真实 MG 缓存 | 拉取/seed | 缓存仍不存在；后来仍到锁屏 |

## 内核是清白的

0083 加了 `SWEET IOX:` 打印。boot21 关键行：

```
SWEET IOX: addInstance IONetworkController
SWEET IOX: class-match IONetworkController -> 1 candidate(s)
SWEET IOX: addMatchingNotification existing=1 sent=1
```

stub 已在 metaclass 实例集里，状态位包含 `kIOServiceMatchedState`，lsd 的
通知也送达了。用户态 block 在 `CFRunLoopRunInMode`（unslid `0x19c57c558`）
空转，没有置成功标志。

## 真正的消费者

`InstalledContentLibrary.__GenerateBuiltInAppInstallSessionID` 在
`0x1b11b9f0c` 调 MG。返回值不是函数的返回对象；函数真正构建的结果在
`x19`。在这个调用点 NOP 是局部的，首启时安全。

## NOP 反汇编

ARM64 指令固定 4 字节、小端。`BL` 编码是 `100101 imm26`；目标 =
`PC + sign_extend(imm26 << 2)`。

```
1b11b9ee0  d10143ff  sub  sp, sp, #0x50        ; 函数序言
1b11b9ef8  955e2759  bl   0x1b6943c5c          ; x19 = 真正返回对象
1b11b9efc  aa0003f3  mov  x19, x0
1b11b9f00  d013d060  adrp x0, 0x1d8bc7000
1b11b9f04  911c2000  add  x0, x0, #0x708       ; x0 = CFString
1b11b9f08  d2800001  mov  x1, #0
1b11b9f0c  955e2502  bl   0x1b6943314          ; <-- 改成 NOP
1b11b9f10  aa0003f4  mov  x20, x0
...
1b11b9f34  d2800014  mov  x20, #0
1b11b9f38  36000060  tbz  w0, #0, 0x1b11b9f44
1b11b9f3c  955e2763  bl   0x1b6943cc8
1b11b9f40  aa0003f4  mov  x20, x0
1b11b9f44  ...
1b11b9f50  a9004ff4  stp  x20, x19, [sp]       ; log/format 参数
1b11b9f5c  9402edf1  bl   0x1b1275720          ; log/format
```

这条调用在序言 `0x1b11b9ee0` 之后 `+0x2c`；返回地址是 `+0x30`
（`0x1b11b9f10`）。`x19`/`x20` 是 callee-saved；调用结果在 `x0`。

解码这条调用：

| 项 | 值 |
|---|---|
| 指令字 | `0x955e2502` |
| 高 6 位 | `100101` = `BL` |
| `imm26` | `0x015e2502` |
| 字节偏移 | `0x015e2502 << 2 = 0x05789408` |
| 目标 | `0x1b11b9f0c + 0x05789408 = 0x1b6943314` |
| 小端字节 | `02 25 5e 95` |

替换为 `NOP`（`0xd503201f`，字节 `1f 20 03 d5`）。

为什么在这个调用点安全：

- `x0` 预载 CFString、`x1` 为 0；调用结果写到 `x20`，不是函数返回寄存器。
- `x19` 由前一个调用载入，是函数构建返回值的对象；NOP 不碰 `x19`。
- 在这个窗口里，`x20` 在 `0x1b11b9f34`/`0x1b11b9f40` 被重写，然后才在
  `0x1b11b9f50` 作为 log/format 参数；MG 结果不会成为返回对象。
- 只改一个 `BL`；callee 被其他调用者共享，改 callee 范围更大、风险更高。

这仍然是**绕过，不是修复**。偏移只对 16.7.16 这个 shared cache 有效；
MG 缓存仍不存在；原块已备份。

## 补丁

| 项 | 值 |
|---|---|
| 子缓存 | `dyld_shared_cache_arm64.15` |
| 文件偏移 | `0x1619f0c` |
| VA | `0x1b11b9f0c` |
| iosroot 4K 块 | `2438140` |
| 块内偏移 | `0xF0C` |
| 原始 | `02 25 5e 95`（`bl`） |
| 补丁 | `1f 20 03 d5`（`nop`） |
| 原始块 SHA256 | `ae3178046fe7cb9e08291c39dc4773429be26c35472c6fbd9135d5f2a225fd73` |
| 补丁块 SHA256 | `4a4895422dcec766b90b65c067ecb06ef8fd3e346c03ee7e2464a85f62a73b74` |

`tools/image/icl_nop.py` 校验原字节/原块 SHA，先备份，再写、fsync、回读。
原块是还原路径。

## 结果

- boot22：Apple logo 后 58 秒到锁屏；时钟连续刷新数分钟。
- boot22（打补丁后首次启动）：58 秒；boot23（热重启）：22 秒到锁屏；
  合成上滑解锁到桌面，动画正常。
- 锁屏日期是 12 月 31 日，时间未同步（无 RTC/NTP），但时钟在走。
- MG 缓存仍不存在：
  `systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist`
  不存在。
- 首启状态部分写入：`installd/Library/MobileInstallation` 多了构建/迁移/角色
  plist 和 SystemGroup UUID 目录；`Journal`/`LaunchServicesOperations` 为空，
  没有 LS DB 或 InstallJournal。
- boot22 diff：62,490 个 4K 块（244 MiB）；数据不在仓库。

## 教训

| 最初判断 | 实际发生 | 教训 |
|---|---|---|
| 内核没送达 | `sent=1`，50+ 次 | 先证明每一环，再怪内核 |
| 需要服务/stub | 送达了仍卡 | 生产者 ≠ 消费者 |
| 超时 patch 能修 | lsd crash-loop | 改等待 ≠ 提供有效结果 |
| 必须有 MG 缓存 | 缓存不存在，锁屏也亮了 | 单个消费者可以绕过 |
| 升级 XNU | 8796/10063 IOKit 函数一致 | 先 diff 再换内核 |
| 锁屏 = 首启完成 | LS DB/Journal 仍缺 | 逐项验证状态 |

## 复现

按工程顺序，而不是一串裸命令：

1. 在自己的 shared cache 里定位 ICL 调用点，核对符号和四个字节
   （`bl` → `nop`）。
2. 算原块 SHA；`icl_nop.py` 先 dry-run。
3. 带备份写入；工具会回读校验。
4. 启动对比；保留原块回滚。
