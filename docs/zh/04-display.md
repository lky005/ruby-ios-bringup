# 04 — 显示

[English](../en/04-display.md) · **中文**

对这个 bring-up 来说，CPU 拷贝显示链路已验证：iOS surface 能上屏，UI 会
刷新。没有 GPU 驱动；这是实测的 framebuffer 拷贝，不是通用显示栈。剩下的
黑壁纸归因于 PosterBoard `[推断]`，不是显示链路。

## 链路

| 阶段 | 值 | 说明 |
|---|---|---|
| iOS surface | 逻辑 1125×2436 | `display-scale=3`，偏移 22/18 |
| IOMFB 服务 | `AppleCLCD` | IOSurface + IOMobileFramebuffer |
| 拷贝区域 | 1080×2400 | surface 中心 → 面板 |
| LK 扫描层 | `0x7cdfc000`，stride 4352 | 实际可见层 |
| Kernel fb/atag 基址 | `0x7ba10000` | 不是可见层 |

```
SpringBoard/CoreAnimation -> IOSurface -> IOMFB -> memcpy -> LK fb -> panel
```

Apple logo 是启动快照 surface，不是 LK 残留帧；拷贝由 IOMFB 驱动，不是
bootloader 交接后还在画。

## 背光

背光与 framebuffer 拷贝是两条独立路径。backboardd 通过 `setProperties`
向 `AppleARMBacklight` 服务下发 `backlight-level`（0–65536，16.16）；
服务再经 MT6877 DSI VM_CMD 寄存器（`0x130/0x134`、START bit 16、
INTSTA bit 5）写 DCS `0x51`，不使用 GCE。

| 项 | 值 |
|---|---|
| 面板 | m16_36_02_0b OLED，12-bit DCS 档位 |
| 曲线 | γ2.6 LUT（33 点），level 0–4095，最小值 8 |
| 平滑 | 跳变 >48 档拆 4 段、每段 10 ms，可被新请求抢占 |
| 失败策略 | 200 ms 超时，下一次请求重试；连续 5 次失败才关闭硬件 |
| 门控 | `rubybacklight=1` 创建服务；`rubyblhw=1` 允许 DSI 写入；两者默认关 |

已验证：G1b 下发 409/2048/409，面板可见亮暗变化；v1.2 亮度条经用户实测
（50% ≈ 470 lx，100% ≈ 1700 lx）。v1.3 的 LUT 与分段仅在 console 验证；
手感与夜览恢复未获用户验收。vendor 内核不带亮度曲线；DCS 档位就是硬件
契约。

## 缓存维护

| 尝试 | 结果 |
|---|---|
| `flush_dcache64(pa, len, TRUE)` | panic：`phys_to_kv_range: illegal PA: 0x7cdfc000` |
| `flush_dcache64((addr64_t)fPixels, len, FALSE)` + `dsb sy` | 正常 |

framebuffer 不在内核管理的物理段，按 PA 刷会 panic；按内核 VA 刷并
`dsb sy` 才正常。

## 证据

- 左上 64×64 品红、中心绿色标记都上屏。
- 日志：`SWEET FB DBG: ... dst_pa=0x7cdfc000 w=1080 h=2400 ...`。
- `src0/srcc/dst0/dstc = 0xff000000/0xffffffff/...` 显示 surface 中心是白色
  Apple logo → 屏幕上是启动快照。
- 锁屏时钟连续刷新数分钟 → 活 UI，不是静态首帧。

## 不是显示问题

| 现象 | 原因 |
|---|---|
| 黑壁纸 | PosterBoard `_stateLock_setupSwitcherConfigurationForFirstTime` 崩溃 [推断] |
| Widget `Waiting...` | WidgetKit/chronod/扩展未就绪 [推断] |
| 分钟刷新时左上短暂白闪 | 状态栏重绘 / surface present 伪影；未解 |
| Messages 红色 badge | 应用安装/启动问题；不阻塞 HID |

不要再追 Apple logo 或面板；显示链路已证明。剩下的外观问题是用户态/扩展
问题。

## 验证

- `tools/image/boot_verify.py <image>` 打印打包 payload 和 cmdline。
- 设备上最快的是看调试标记是否上屏。
- 显示工具不写设备；用离线镜像校验。
