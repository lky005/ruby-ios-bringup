# Device situation

**English** · [中文](../zh/device.md)

This is a description, not a device-baseline hash manifest. Hashes of the GPT,
`boot_a/b`, `vbmeta` or partition GUIDs are intentionally **not** published:
they can fingerprint the unit. The success-contract artifact hashes are in
`config/0085.env` (`config/0084.env` is the previous synthetic-swipe milestone).

## The unit

| Item | Value |
|---|---|
| Device | Redmi Note 12 Pro 5G, `ruby` / MT6877 (Dimensity 1080) |
| Memory / storage | 8 GB + 256 GB |
| System | Android 12 / MIUI 13.0.4, unlocked bootloader, Magisk, slot `_a` |
| Partition layout | `userdata` 208.4 GiB + `iosroot` 17 GiB; `boot_a` 128 MiB; `super` ~9.1 GB |
| Current state | `boot_a` holds the 0084 XNU image; Android not restored; `iosroot` holds the ICL NOP |
| Success artifacts | 0085 real-touch boot image/kernel, 0084 boot image, root image, ICL blocks, boot cmdline |

## What must match

- firmware and GPT layout (the device must be the same `ruby` class);
- the root image hash and the 0085 real-touch boot image hash (`0084` is the
  previous milestone);
- the boot cmdline in `config/0085-boot.cmdline` (or `0084-boot.cmdline` for
  the synthetic-swipe image);
- the panel/display path (1080×2400, LK scan buffer `0x7cdfc000`).

## What does not need to match

Touch firmware, Wi-Fi, USB, GPU and RTC are not part of the success path.

## Testing status

A real-touch 0085 boot (real bottom-edge unlock, two-contact HID dispatch,
edge; user-visible pinch not separately instrumented) and the
0084 home-screen/CI-kernel boots were observed on the author's unit on
2026-10-22; no second unit or clean-room has been tested. CI builds the kernel
only. See
[`../../GUARANTEE.md`](../records/GUARANTEE.md) for the exact guarantee and the
deferred tests.
