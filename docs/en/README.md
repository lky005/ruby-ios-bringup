# Documentation (English)

**English** · [中文](../zh/README.md)

Evidence-first. Each claim is tagged **[measured]**, **[DTS]**, **[inferred]**
or **[historical]**. Unverified claims are not presented as facts. There are no
personal paths, device identifiers or Apple binaries here.

## Reading paths

| Time | Read | Goal |
|---|---|---|
| 5 min | `../../README.md`, `../../STATUS.md` | what works, what does not |
| 30 min | `08-recovery`, `09-reproduce`, `10-scripts` | build, flash, recover |
| Deep | `01`–`07` | mechanisms, evidence, wrong turns |

## Chapters

| Doc | Contents |
|---|---|
| [`01-architecture`](01-architecture.md) | boot chain and component map |
| [`02-hardware`](02-hardware.md) | measured MT6877 coordinates |
| [`03-boot-chain`](03-boot-chain.md) | LK, 128 MiB image, WDT/console |
| [`04-display`](04-display.md) | surface to panel, cache maintenance |
| [`05-userland`](05-userland.md) | launchd/LS/MG deadlock, ICL NOP disassembly |
| [`06-input`](06-input.md) | real Goodix touch, SweetHID, edge tip, autoswipe |
| [`touch-goodix-9916r`](touch-goodix-9916r.md) | GT9916R hardware, power/protocol manual, bring-up history |
| [`07-experiments`](07-experiments.md) | timeline, failure catalogue, decisions |
| [`08-recovery`](08-recovery.md) | Android restore, TWRP, raw I/O |
| [`09-reproduce`](09-reproduce.md) | build, pack, flash, verify |
| [`10-scripts`](10-scripts.md) | per-script purpose and boundaries |
| [`11-ci-baseline`](11-ci-baseline.md) | content-pinned baseline, branch pins, exec-data gates |
| [`appendix-dualboot`](appendix-dualboot.md) | optional layout; method note only |
| [`glossary`](glossary.md) | codenames, acronyms and status tags |
| [`device`](device.md) | device situation; no baseline hashes |
| [`root-recipe`](root-recipe.md) | root inputs and steps; no root image |
| [`reproducibility`](reproducibility.md) | Tier B recipe, drift controls, deferred tests |
| [`Guarantee`](../../GUARANTEE.md) | success-path scope, bundle hashes, deferred tests |

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
