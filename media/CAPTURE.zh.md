# 媒体拍摄规范

[English](CAPTURE.md) · **中文**

首批脱敏素材已入库：[`home-screen.jpg`](home-screen.jpg) 和
[`autoswipe.mp4`](autoswipe.mp4)（2026-10-21）。后续拍摄仍按这份清单；
`lock-screen.jpg` 和 `boot.mp4` 尚未提供。

## 拍什么

| 文件 | 内容 | 格式 |
|---|---|---|
| `lock-screen.jpg` | 能看到时钟的锁屏 | JPEG，<1 MB |
| `home-screen.jpg` | SpringBoard 桌面，含 Dock | JPEG，<1 MB |
| `autoswipe.mp4` | 锁屏 → 上滑 → 桌面 | H.264，720p，10–20 秒，<10 MB |
| `boot.mp4` | Apple logo → 锁屏（可选） | H.264，720p，<10 MB |

## 脱敏

- 去掉 EXIF/GPS 和所有元数据；图片/视频重新编码。
- 用演示数据/飞行模式；不要出现通知、Apple ID、运营商名、短信、照片或
  账号头像。
- 检查状态栏和反光里有没有序列号、IMEI 或个人信息。
- 不想公开的内容裁掉或模糊。
- 不要拍设备序列号、包装标签或购买记录。
- 主机检查会用一份私有的敏感词清单扫描公开树、暂存 diff 和最近的提交信息，
  命中即失败；清单本身不进仓库。

## 命名与来源

用上面的文件名。在 `media/README.md` 写短说明：日期、构建 SHA（0084 镜像
或内核）、画面内容。记录每个文件的 SHA256。

## 体积与托管

图片 <1 MB，视频 <10 MB。更大的视频放 release asset 或外部托管并给链接；
不要提交大二进制。

## 提交规则

媒体是可选项。缺一张照片，比泄露一条通知或元数据好。拿不准就不提交。
