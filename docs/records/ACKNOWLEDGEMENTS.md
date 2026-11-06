# Acknowledgements

**English** · [中文](ACKNOWLEDGEMENTS.zh.md)

This project builds on open-source and community work. No upstream tree is
copied into this repository; the pinned baseline is fetched at build time.

## Upstream projects

- [ios-sweet](https://github.com/dipa-studio/ios-sweet) — the original
  iOS-on-Sweet project; the userland/display/UFS ideas and the patch lineage.
- [ios-topaz](https://github.com/MakrSas/ios-topaz) — the topaz port and the
  pinned build baseline.
- [blacktop/darwin-xnu-build](https://github.com/blacktop/darwin-xnu-build) —
  the MIT-licensed XNU build harness used by the workflow.
- [Apple XNU](https://github.com/apple-oss-distributions/xnu) — the open-source
  kernel; patches remain under APSL 2.0.
- [Xiaomi ruby-s-oss](https://github.com/MiCode/Xiaomi_Kernel_OpenSource) —
  the device tree and driver reference.
- [TWRP](https://twrp.me) — recovery environment; no TWRP image is included.
- [Magisk](https://github.com/topjohnwu/Magisk) — Android root; no Magisk image
  is included.

The iPhone X iOS 16.7.16 userland and Apple firmware belong to Apple. They are
not included; users must obtain their own copy and comply with Apple's terms.

## Tooling and assistance

Analysis, documentation and code review were assisted by LLM/agent tools,
including DeepSeek and other models. The author is responsible for all device
results; claims are backed by the artifacts, logs and hashes in this repository,
not by model output. LLM output is not a source of truth.

## Corrections

If an attribution is missing or wrong, open an issue with the exact file and
commit. Do not include personal or device-identifying data in the report.
