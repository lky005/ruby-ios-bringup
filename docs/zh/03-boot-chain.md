# 03 — 启动链与镜像布局

[English](../en/03-boot-chain.md) · **中文**

LK 只认完整 128 MiB + stock kernel 流大小的镜像；其余配方都是它的变体。

## LK 启动链

```
Xiaomi preloader -> LK（已解锁）
  -> 读 boot_a（Android boot v2，page 2048）
  -> gzip kernel -> 0x40080000
  -> ramdisk -> 0x51100000
  -> MTK DTB 头 + DTB -> 0x47c80000
  -> jump K64，EL1h，x0 = DTB
```

LK 日志特征：

```
booting linux @ 0x40080000, ramdisk @ 0x51100000
[LK]jump to K64 0x40080000
boot linux-64 via EL2, x0=0x47c80000
```

出现 `jump to K64` 且没有 `hdr_loaded`/`decompress`/`panic`，说明镜像被接受、
payload 已执行。

## 完整 128 MiB 布局

| 项 | 值 | 说明 |
|---|---|---|
| 分区大小 | 134,217,728 B | 128 MiB |
| Header | Android v2，page 2048 | `ANDROID!` |
| Kernel 流 | 16,606,685 B gzip | 精确 stock 大小 |
| Kernel load | `0x40080000` | |
| Ramdisk | 17,876,407 B（Magisk） | stock 17,634,771 |
| Ramdisk load | `0x51100000` | |
| DTB 偏移 | `0x20e3800` | Magisk 布局；stock `0x20a8800` |
| AVB0 | `0x210e000` | |
| AVB footer | `0x7ffffc0` | 分区最后 4 KiB |

36.7 MB 镜像会留下不匹配的 AVB footer；整镜像把 DTB/AVB0/footer 保持在
stock 偏移。

## 小 payload（红屏）

1. 取 stock/Magisk 整镜像，解压 kernel 到 37,449,728 B。
2. 保留 ARM64 Image 头（`ARM\x64` 在 raw+0x38）。
3. raw[0:4] 改成分支到 `0x1000`（`0x14000400`）。
4. payload 放到 raw+0x1000。
5. 重新 gzip 到**精确** 16,606,685 B（FEXTRA 补齐，无尾部零）。
6. 写回，保持 DTB/ramdisk/AVB 位置不变。

成功判据：屏幕整块变红；LK expdb 有 `jump to K64`。

## Shim 配方

1. shim 链接到 `0x40080000`，自带 Linux Image 头。
2. 解压 raw kernel，清零，写入 shim，补齐到 `_end`。
3. 剩余空间填充，使 gzip 流达到 stock 大小；FEXTRA 精确补到 16,606,685。
4. 保持 DTB/ramdisk/footer 位置。

早期打包器在 `src/bringup/`；0085/0084 镜像用了上游 loader + ADT 构建器，
仓库没有把这一部分复制进来。

## FEXTRA 细节

- gzip FLG=0x04；XLEN 是补齐长度。
- 压缩流总长必须等于 stock `kernel_size`。
- 不能有尾部零字节。
- 参考：`src/bringup/build_full_a.py`、`build_shim_full.py`。

## 为什么放弃 b 槽

| 尝试 | 结果 |
|---|---|
| 4 KB 自定义镜像 | 传输超时 / `can't find v2 dtb` |
| 18 MB kernel + DTB | `can't find v2 dtb` / `img_loaded` |
| 36.7 MB stock 布局 | `decompress kernel image fail` |
| 36.7 MB gzip | `hdr_loaded` panic |
| 已知可启动 boot_a 镜像刷到 b | **同样 `hdr_loaded`** |
| 禁用 vbmeta_b | 仍 `hdr_loaded` |

b 槽的 header/AVB 路径本身有问题；用 `_a`，并用已知可启动整镜像恢复。

## Console 与看门狗

- 可见 LK 层：`0x7cdfc000`，stride 4352；第二层 `0x7c406000`。
- 早期 shim 写 `0x7ba10000`，屏幕不可见；v2 改用 `0x7cdfc000`。
- LK 开启 MTK TOPRGU `0x10007000`；写 `0x22000000` 关闭，自旋/panic 循环喂
  `0x10007008 = 1`。
