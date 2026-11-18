# 05 — Userland: LS/MG and the ICL NOP

**English** · [中文](../zh/05-userland.md)

The lock-screen wall looked like a kernel notification bug. It was not: the
kernel delivered `IOServiceMatched`, but a userland MobileGestalt consumer was
stuck in a run-loop/semaphore. The 4-byte ICL NOP bypasses that consumer.

## Symptom

```
lsd t0: _LSServerCleanEphemeralMobileContainersForFirstBoot
        -> performJournalRecovery -> dispatch_sync

lsd t1: dispatch_semaphore_wait_slow
        <- MGIOKitSupport helper
        <- libMobileGestalt
        <- MIInstallationIdentity
        <- InstalledContentLibrary __GenerateBuiltInAppInstallSessionID
```

SpringBoard t0 waits on `_LSContextInitCommon`; t1 holds the lock and waits for
lsd. The two lsd threads wait on each other through the MG path.

## Ruled out

| Hypothesis | Experiment | Result |
|---|---|---|
| CPU count / A78 | `cpus=6` + upstream cache | stacks byte-identical to `cpus=8` |
| launchd cache variant | upstream vs boot-forced | no change |
| ADT lacks Wi-Fi node | add `/arm-io/marconi-wifi` | matches `IOPlatformDevice`, still no `IONetworkController` notification |
| No IONetworkController service | kernel 0082 stub | stub published; notification delivered 0 times in that boot |
| Semaphore timeout | `mov x1,#-1` → `#0` | lsd left the wait but crash-looped (`ns 2 code 0xa`) |
| Need real MG cache | pull/seed attempts | cache still absent; lock screen still reached later |

## The kernel was clean

0083 added `SWEET IOX:` prints. boot21 showed:

```
SWEET IOX: addInstance IONetworkController
SWEET IOX: class-match IONetworkController -> 1 candidate(s)
SWEET IOX: addMatchingNotification existing=1 sent=1
```

The stub was in the metaclass instance set, the state had
`kIOServiceMatchedState`, and lsd's notification was delivered. The userland
block was looping in `CFRunLoopRunInMode` (unslid `0x19c57c558`) and never set
its success flag.

## The real consumer

`InstalledContentLibrary.__GenerateBuiltInAppInstallSessionID` calls MG at
`0x1b11b9f0c`. The return value is not the function's return object; the
function builds its result in `x19`. NOP-ing this call is local to the call
site and safe for first boot.

## NOP disassembly

ARM64 instructions are fixed 4 bytes and little-endian. `BL` is
`100101 imm26`; the target is `PC + sign_extend(imm26 << 2)`.

```
1b11b9ee0  d10143ff  sub  sp, sp, #0x50        ; function prologue
1b11b9ef8  955e2759  bl   0x1b6943c5c          ; x19 = real result object
1b11b9efc  aa0003f3  mov  x19, x0
1b11b9f00  d013d060  adrp x0, 0x1d8bc7000
1b11b9f04  911c2000  add  x0, x0, #0x708       ; x0 = CFString
1b11b9f08  d2800001  mov  x1, #0
1b11b9f0c  955e2502  bl   0x1b6943314          ; <-- patched to NOP
1b11b9f10  aa0003f4  mov  x20, x0
...
1b11b9f34  d2800014  mov  x20, #0
1b11b9f38  36000060  tbz  w0, #0, 0x1b11b9f44
1b11b9f3c  955e2763  bl   0x1b6943cc8
1b11b9f40  aa0003f4  mov  x20, x0
1b11b9f44  ...
1b11b9f50  a9004ff4  stp  x20, x19, [sp]       ; log/format arguments
1b11b9f5c  9402edf1  bl   0x1b1275720          ; log/format
```

The call is at `+0x2c` from the prologue at `0x1b11b9ee0`; the return address
is `+0x30` (`0x1b11b9f10`). `x19` and `x20` are callee-saved; the call's result
arrives in `x0`.

Decode the call:

| Item | Value |
|---|---|
| Instruction word | `0x955e2502` |
| Top 6 bits | `100101` = `BL` |
| `imm26` | `0x015e2502` |
| Byte offset | `0x015e2502 << 2 = 0x05789408` |
| Target | `0x1b11b9f0c + 0x05789408 = 0x1b6943314` |
| Little-endian bytes | `02 25 5e 95` |

Replace it with `NOP` (`0xd503201f`, bytes `1f 20 03 d5`).

Why this is safe at this site:

- `x0` is preloaded with a CFString and `x1` is zero; the call's result goes to
  `x20`, not to the function's return register.
- `x19` is loaded from an earlier call and is the object the function builds
  its result from; the NOP does not touch `x19`.
- In this window `x20` is reassigned at `0x1b11b9f34`/`0x1b11b9f40` before it
  is stored for the log/format at `0x1b11b9f50`, so the MG result does not
  become the returned object.
- The call site is one `BL`; the callee is shared by other callers, so patching
  the callee would be broader and riskier.

This is still a **bypass, not a fix**. The offset is specific to this
16.7.16 shared cache; the MG cache is still absent; the original block is
backed up.

## Patch

| Item | Value |
|---|---|
| Subcache | `dyld_shared_cache_arm64.15` |
| File offset | `0x1619f0c` |
| VA | `0x1b11b9f0c` |
| iosroot 4K block | `2438140` |
| In-block offset | `0xF0C` |
| Original | `02 25 5e 95` (`bl`) |
| Patched | `1f 20 03 d5` (`nop`) |
| Original block SHA256 | `ae3178046fe7cb9e08291c39dc4773429be26c35472c6fbd9135d5f2a225fd73` |
| Patched block SHA256 | `4a4895422dcec766b90b65c067ecb06ef8fd3e346c03ee7e2464a85f62a73b74` |

`tools/image/icl_nop.py` validates the original bytes/block SHA, writes a
backup, patches, fsyncs and re-reads. The original block is the restore path.

## Result

- boot22: 58 s from Apple logo to lock screen; clock refreshed for minutes.
- boot22 (first boot after the patch): 58 s; boot23 (warm reboot): 22 s to
  the lock screen; synthetic swipe unlocked to the home screen; animations
  normal.
- The lock screen date was `Wednesday, December 31` and the clock was not
  synced (no RTC/NTP), but time advanced.
- MG cache is still absent:
  `systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist`
  does not exist.
- First-boot state is partial: `installd/Library/MobileInstallation` gained
  build/migration/role plists and SystemGroup UUID dirs; `Journal` and
  `LaunchServicesOperations` were empty; no LS DB or InstallJournal found.
- boot22 diff: 62,490 changed 4K blocks (244 MiB); the data is not in this repo.

## Lessons

| First guess | What happened | Lesson |
|---|---|---|
| Kernel did not deliver | `sent=1`, 50+ times | prove each hop before blaming the kernel |
| Need a service/stub | delivered, still stuck | producer ≠ consumer |
| Timeout patch will fix it | lsd crash-loop | changing a wait ≠ providing a valid result |
| Must have MG cache | cache absent, lock screen live | a single consumer can be bypassed |
| Upgrade XNU | 8796/10063 IOKit functions identical | diff before swapping kernels |
| Lock screen = first boot done | LS DB/Journal still absent | verify state item by item |

## Reproduce

The engineering sequence, not a bare command list:

1. Identify the ICL call site in your own shared cache; verify the symbol and
   the four bytes (`bl` → `nop`).
2. Compute the original block SHA; run `icl_nop.py` in dry-run.
3. Apply with a backup; the tool re-reads the block.
4. Boot and compare; keep the original block for rollback.
