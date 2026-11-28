# 15 — GPU: kernel driver and userland research line

**English** · [中文](../zh/15-gpu.md)

> Status: **experimental**. The kernel face (0352/0360) is merged and
> CI-verified; the userland stack (Mesa PanVK, Metal-on-Vulkan shim) lives on
> the lab line and is documented here for the record. The 0360 kernel has
> **no boot record**: it is gated by the same patchset/exec-data checks as
> every other line, but it has not been flashed.

## 1. Stack

```text
iOS apps (Metal)                         GL/Vulkan apps
  │ Metal.framework                        │ libGLESv2 / libvulkan
  │ (research shim: AIR→SPIR-V)            │ (Mesa Panfrost/PanVK port)
  ▼                                        ▼
RubyGPU service (XNU kext: device, power, MMU, BO, submit, context)
  │ INTID487 IRQ, SG-backed BOs, per-task surface ownership
  ▼
Mali-G68 (MT6877 MFG, 2×EE / 1×JS, job slots, 16 KiB pages)
```

Two kernel faces exist:

- **0352** — read-only probe plus a gated power path. It dumps the Mali
  register windows (GPU_ID, AS/JS_PRESENT, READY bits), the mfgcfg window
  (CG/ASYNC/QCHANNEL/DEBUG/I2M), the SPM status window, TOP/infra bus-protect,
  the MFG PLL and the MT6359P VPROC2/VSRAM_MD registers over the pwrap read
  channel. Gated by `rubygpuprobe=1` (default off, no writes, runs once). The
  MFG2-5 power-on path is gated by `rubygpupwr=2` (default off).
- **0360** — the driver face recovered from the lab line (see §2).

## 2. Kernel face (0360)

| Area | File(s) | Notes |
|---|---|---|
| Driver core | `iokit/Kernel/arm/RubyGPU.cpp/.h` | Device discovery, power sequencing, MMU, BO management, submit, context lifetime; writes nothing unless the line asks for it |
| IRQ | `RubyGPUIRQ.cpp/.h` | INTID487, job/fault completion |
| Userclient | `RubyGPUUserClient.cpp/.h`, `RubyGPUUserAPI.h` | Panfrost kmod surface subset: BO create/release, VM create/bind/unbind, submit, sync |
| Surfaces | `SweetSurface.cpp/.h` | Per-task ownership; only the task that created a surface may import it into a BO (kernel-published panel surfaces are never importable) |
| Metal hook | `RubyGPU.cpp` (`IOAcceleratorES`) | Empty IORegistry service so a native Metal plugin can be discovered; `MetalPluginName`/`MetalPluginClassName` properties are settable only with `rubymetalu=1` (default off) |
| Diagnostics | `IOUserClient.cpp`, `RubyGPU.cpp` | `rubygpudiag=1` selector-8 tracing and driver dumps, console-ring capped, default off |
| Display | `SweetFramebuffer.cpp` | 60 Hz flush default (`sweetfb_hz=10` restores the old throttle) and a driver commit hook |
| CPU B4a | `pexpert` `SWEET.h`/`board_config.h`, `sched_clutch.c`, `sweet_sample.c` | AMP face: two clusters, Edge default placement (P buckets on the first P cluster, UT/BG on the boot cluster), read-only clock probe. Needs a 2-cluster ADT to take effect; no ADT is shipped and the A78 cluster stays at 650 MHz (no DVFS) |

BO accounting is bounded (`rubygpubomax`, `rubygpuvmpages`) with userland
release; the lab line runs stable at `live_buf=5 live_tex=31 imports=4`.

## 3. Mesa / PanVK line (separate repository, planned)

- Mesa 27.0.0-devel pin `49f13b7`, iOS arm64 cross build; x86_64 host build
  generates the v9 shader pregen, the iOS build consumes it.
- Panfrost GL (GLES 3.1) reaches the device; PanVK v9 uses a
  JimVulkan-derived v9 userland on top of the same XNU kmod backend.
- Gate A (x86_64 clean build, 1212/1212 targets) and Gate B (iOS cross build)
  both pass; a device GL test renders native 1080×2400 through the panel
  surface.
- Packaging: patches + build scripts + pregen, no vendored Mesa tree. A
  dedicated public repository is planned; it is not part of this kernel repo.

## 4. Metal-on-Vulkan shim (separate repository, planned)

- A Metal plugin bundle (`RubyMetal.bundle`) implements `_MTLDevice` over
  PanVK; QuartzCore hooks and AIR→SPIR-V translation are research.
- Milestones: plugin loading and P37Device bring-up, render-target/copy-blit
  paths, texture sampling, alpha blending, a red probe composited on screen,
  and a surface write-back path with Y-flip (lock-screen indicator visible).
- Not working: full SpringBoard composition (white content, sliding black
  bands), 10-bit color (approximated as BGRA8). Two userland freezes were
  observed and recovered by reset; root cause unknown.
- The shim depends on the Mesa repository's ICD; it is planned as its own
  public repository with an explicit experimental status.

## 5. Verified state

| Stage | Result |
|---|---|
| P1 read-only probe (0352) | PASS: GPU_ID/AS/JS_PRESENT/READY, mfgcfg, SPM, bus-protect, MFG PLL decoded on device |
| P2 gated power-on | PASS: MFG2-5 rails/clock sequence under `rubygpupwr=2` |
| P3.1/P3.2 driver + userclient | PASS on device (UAPI round-trips, submit `kr=0`) |
| P3.4 display | PASS: native 1080×2400 swap through the panel surface (SG BO allocation) |
| P3.5 PanVK | PASS: GL test renders; ~26 fps batch-sync baseline |
| P3.6 PanVK submit | PASS: batch-sync path retained (double-buffering reverted); ~26 fps baseline unchanged |
| Metal shim (M0–M9b v12) | Research: plugin loads, red probe on screen, real composition WIP |
| 0360 kernel | CI-verified only, never booted |

## 6. Boot arguments

See [appendix-bootargs](appendix-bootargs.md) for the full 0360 boot line and
the parameter table (`rubygpuprobe`, `rubygpupwr`, `rubygpucommit`,
`rubygpuuc`, `rubygpumulti`, `rubygpubomax`, `rubygpuvmpages`, `rubymetalu`,
`rubygpudiag`, `sweetfb_hz`). All GPU gates default off.

## 7. Building the kernel face

```sh
# patchset: bd125daf (327 files); exec-data 4fef9a18
ALLOW_PUBLIC_UPSTREAM=1 sh ci/prepare-baseline.sh <dest>
python3 scripts/verify-local.py --ci-config config/0360.env
# CI: run the xnu-0360 workflow (macos-15, Xcode 16.0); record then gated run
```

The 0352 line is `config/0352.env` (patchset `40f7cefa`, 318 files,
exec-data `90326b5e`). Record and gated run ids are in
[VERIFICATION](../records/VERIFICATION.md).

## 8. Not guaranteed

- No frame rate, composition correctness or Mesa packaging guarantee.
- The 0360 kernel is not booted; B4a AMP needs a 2-cluster ADT that is not
  shipped.
- The Metal shim is research: white-content composition and 10-bit color are
  open problems, and the two userland freezes on the lab line are unresolved.
- The GPU work assumes a single device unit and lab-line images; it is not a
  supported configuration.