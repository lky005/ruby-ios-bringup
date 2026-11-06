# Documentation (English)

**English** · [中文](../zh/README.md)

Evidence-first. Each claim is tagged **[measured]**, **[DTS]**, **[inferred]**
or **[historical]**. Unverified claims are not presented as facts. There are no
personal paths, device identifiers or Apple binaries here.

## Current line

| Item | Value |
|---|---|
| Line | 0195 |
| `main` / tag | `1e45453` / `v0.6.0` |
| Patchset | `a9cc0050…` (187 files) |
| Kernel | full `45ea1bc3…`, exec-data `6b22fc25…` |
| Image | `fe009b89…` (`x16-0195-ack.img`; golden boot verified on 0194 `1808e440…`) |
| Known limits | XactErr `0xC0000011`; 511 B framing; host-port drop under clear storms; no USB host/audio/Wi-Fi/BT/camera/GPU/RTC/sleep; research bring-up |

See [STATUS](../records/STATUS.md) · [VERIFICATION](../records/VERIFICATION.md) · [GUARANTEE](../records/GUARANTEE.md).

## Reading paths

| Time | Read | Goal |
|---|---|---|
| 5 min | `../../README.md`, `../../STATUS.md` | what works, what does not |
| 30 min | `08-recovery`, `09-reproduce`, `10-scripts` | build, flash, recover |
| Deep | `01`–`07` | mechanisms, evidence, wrong turns |

## Chapters

| Doc | Contents | Status | Last verified |
|---|---|---|---|
| [`01-architecture`](01-architecture.md) | boot chain and component map | `[measured]` | 2026-10-22 |
| [`02-hardware`](02-hardware.md) | measured MT6877 coordinates | `[measured]` | 2026-11-06 |
| [`03-boot-chain`](03-boot-chain.md) | LK, 128 MiB image, WDT/console | `[measured]` | 2026-10-22 |
| [`04-display`](04-display.md) | surface to panel, cache maintenance | `[measured]` | 2026-10-22 |
| [`05-userland`](05-userland.md) | launchd/LS/MG deadlock, ICL NOP disassembly | `[measured]` | 2026-10-22 |
| [`06-input`](06-input.md) | real Goodix touch, native EINT14, keys, SweetHID, edge tip, autoswipe | `[measured]` | 2026-11-06 |
| [`touch-goodix-9916r`](touch-goodix-9916r.md) | GT9916R hardware, power/protocol manual, native EINT service, bring-up history | `[measured]` | 2026-11-06 |
| [`07-experiments`](07-experiments.md) | timeline, failure catalogue, decisions | `[measured]` | 2026-11-06 |
| [`08-recovery`](08-recovery.md) | Android restore, TWRP, raw I/O | `[measured]` | 2026-10-22 |
| [`09-reproduce`](09-reproduce.md) | build, pack, flash, verify | `[measured]` | 2026-11-06 |
| [`10-scripts`](10-scripts.md) | per-script purpose and boundaries | `[measured]` | 2026-11-06 |
| [`11-ci-baseline`](11-ci-baseline.md) | content-pinned baseline, branch pins, exec-data gates | `[measured]` | 2026-11-06 |
| [`12-usb-host`](12-usb-host.md) | USB host channel: test conditions, driver binding, safe debugging | `[measured]` | 2026-11-06 |
| [`13-usb-ep2-golden`](13-usb-ep2-golden.md) | EP2 state machine 0180–0195, golden PHY, host-side limits | `[measured]` | 2026-11-07 |
| [`appendix-dualboot`](appendix-dualboot.md) | optional layout; method note only | `[inferred]` | — |
| [`glossary`](glossary.md) | codenames, acronyms and status tags | — | — |
| [`device`](device.md) | device situation; no baseline hashes | `[measured]` | 2026-10-22 |
| [`root-recipe`](root-recipe.md) | root inputs and steps; no root image | `[measured]` | 2026-10-22 |
| [`reproducibility`](reproducibility.md) | Tier B recipe, drift controls, deferred tests | `[measured]` | 2026-11-06 |
| [`Guarantee`](../records/GUARANTEE.md) | success-path scope, bundle hashes, deferred tests | `[measured]` | 2026-11-06 |

## Rules

- A number without a source is a bug. Cite live FDT, a log line, a SHA or a
  command that can be re-run.
- Label `[measured]` / `[inferred]` / `[historical]`; never upgrade a guess to
  a fact.
- Commands use placeholders (`<base>`, `<out>`, `<workdir>`), never personal
  paths.
- No Apple firmware, iOS root, shared cache, device dumps, serials, IMEI/MAC or
  account data.
- Every script entry states what it does **not** do and how to fail safely.
