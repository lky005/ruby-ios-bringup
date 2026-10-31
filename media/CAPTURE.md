# Media capture plan

**English** · [中文](CAPTURE.zh.md)

The first sanitized assets are committed: [`home-screen.jpg`](home-screen.jpg)
and [`autoswipe.mp4`](autoswipe.mp4) (2026-10-21). Use this checklist for
future captures; `lock-screen.jpg` and `boot.mp4` are still open.

## What to capture

| Asset | Content | Format |
|---|---|---|
| `lock-screen.jpg` | lock screen with the clock visible | JPEG, <1 MB |
| `home-screen.jpg` | SpringBoard home screen, dock visible | JPEG, <1 MB |
| `autoswipe.mp4` | lock screen → swipe → home screen | H.264, 720p, 10–20 s, <10 MB |
| `boot.mp4` | Apple logo → lock screen (optional) | H.264, 720p, <10 MB |

## Sanitization

- Strip EXIF/GPS and all metadata; re-encode images/video.
- Use demo data / airplane mode; no notifications, Apple ID, carrier name,
  messages, photos, or account avatars.
- Check the status bar and reflections for serial numbers, IMEI or personal
  information.
- Crop or blur anything you do not want public.
- Do not show a device serial, box label, or purchase record.
- The host check scans the public tree, the staged diff and recent commit
  messages against a private list of device identifiers and fails on a hit. The
  list itself never enters the repository.

## Naming and provenance

Use the names above. Add a short caption in `media/README.md` with date, build
SHA (0084 image or kernel), and what is shown. Record the SHA256 of each file.

## Size and hosting

Keep images under 1 MB and clips under 10 MB. If a clip is larger, upload it as
a release asset or host it externally and link it; do not commit large binaries.

## Commit rule

Media is optional. A missing photo is better than a leaked notification or
metadata. When in doubt, do not commit it.
