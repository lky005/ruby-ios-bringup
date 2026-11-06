# 01 — 架构

[English](../en/01-architecture.md) · **中文**

这个项目是一串小替换，不是“把内核搬过去”一件事。这一页放好所有组件，
并标出项目增量的位置。

## 启动链

```
Xiaomi preloader
  -> LK（已解锁）
     -> boot_a：Android boot v2，128 MiB
        -> kernel 槽：gzip 流，精确 16,606,685 字节
           -> shim/loader（raw AArch64）@ 0x40080000
              -> XNU 8796 + ADT + boot args
                 -> UFS LUN 2 -> HFS+ root（iosroot）
                    -> dyld + launchd -> lsd -> backboardd -> SpringBoard
                       -> 显示：IOSurface/IOMFB -> LK framebuffer
                       -> 输入：SweetHID -> IOHIDEventService
```

LK 没有 `boot:`，所以每次实验都刷 `boot_a`。128 MiB 整镜像保持 DTB、AVB0、
AVB footer 在 stock 偏移，避免 `hdr_loaded` 拒绝。

## 分层

| 层 | 组件 | 本项目增量 |
|---|---|---|
| Bootloader | 小米 LK | 无；只写 `boot_a` |
| Payload | shim/loader | 早期 `src/bringup`；0084 用上游 loader |
| 内核 | XNU 8796 | 补丁 0080/0085（真实触摸）、0156-0179（HAL/USB/电池/原生 IRQ）；0084 上一里程碑；0081–0083 历史 |
| Root | `iosroot` 上的 HFS+ | pulled v14 + seed；不在仓库 |
| 用户态 | iOS 16.7.16 | ICL 4 字节 NOP |
| 显示 | IOSurface/IOMFB | 0081 调试路径 |
| 输入 | SweetHID | 真实 Goodix 触摸，0179 起由原生 EINT14 驱动（0085 bit-bang 轮询为历史）；保留 0084 合成上滑 |

## 三堵墙

1. **镜像布局。** LK 只认完整 128 MiB + stock kernel 流大小；36.7 MB 镜像会
   留下不匹配的 AVB footer。
2. **显示。** 可见 buffer 是 `0x7cdfc000`、pitch 4352；按 PA 刷 cache 会
   panic，按内核 VA 刷才正常。
3. **用户态。** lsd 首启 journal recovery 等一个 MobileGestalt 消费者；
   内核通知其实已送达。ICL NOP 绕过的是消费者，不是内核。

## 仓库边界

仓库只拥有增量、工具和证据；Apple 用户态、iOS root、boot 镜像和上游基线
都不在仓库里。
