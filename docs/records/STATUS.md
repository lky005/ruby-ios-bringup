# Status

As of **2026-11-07**. This is a snapshot of verified results, not a live device
status. No phone is attached to this repository or to its CI.

## Verified

| Item | Result | Evidence |
|---|---|---|
| Boot to lock screen | first boot ~60 s (58 s measured); warm reboot ~22 s (boot23) | timings from the Apple logo; author's device log; 0084 image SHA `94c639d1...` |
| Unlock to home screen | synthetic swipe; normal animations | author's device log and screen capture |
| ICL NOP | dyld `.15`, iosroot 4K block `2438140`, `02255e95 -> 1f2003d5` | original block SHA `ae317804...`; patched `4a489542...`; backup exists |
| UFS root | LUN 2, GPT header at 512 / entries 1024, `iosroot` partition | read/write HFS+ mount on the author's device |
| Display | IOSurface/IOMFB to LK framebuffer; 1080x2400 | surface markers and live UI |
| HID path | `SweetHIDTouch -> IOHIDEventService -> backboardd -> SpringBoard` | synthetic autoswipe + real touch reach SpringBoard |
| Real touch | Goodix GT9916R/BerlinD over bit-bang SPI3; bottom-edge unlock, two-contact HID dispatch, edge events | 0085 boot 2026-10-22; `SWEET GT` init log, 206 down/206 up and 40 finger-1 kernel records; user-visible pinch not separately instrumented; see `docs/en/touch-goodix-9916r.md` |
| Native touch IRQ | EINT14 edge → EINT child controller → dedicated IOWorkLoop oneshot → SPI3/HID → `service_done` re-arm; `gt_thread` removed; commands/diagnostics on `IOCommandGate`; 1–5-finger HID frames | 0179 device run 2026-11-06; G1–G6; first 10 min `isr 2381→6004`, `ok=5997`, `fail=7`; ~5 min stress `isr 8672→13282`, `ok=12866`, `fail +9`; no panic/stuck/re-activation |
| Patch checks | 0084/0083/0081 apply to the pre-0084 build tree; 0080/0082 are already applied; 0085 applies after 0084 and built successfully | host-side `git apply --check`; CI run `39694456200` |
| ICL tool | original block -> patched block reproduces `4a489542...` | host-side round-trip, 2026-10-21 |
| Host pipeline | payload `50701e81...`; deterministic rebuild `a0ce0fe1...`; layout PASS vs 0084 | host-only, 2026-10-21; no root/phone |
| Host checks | strict host bundle PASS; config-mode layout PASS (11 checks); Linux host CI green before the final docs/template-only amendment | host-only, 2026-10-21 |
| Root state audit | A `e698339d...` (post-boot22), B `985c30...` (pre-boot22), C `34c2882d...` (clean base), A' `55e2ab2c...` (first-boot snapshot) | read-only audit, 2026-10-22 |
| First boot from B+NOP | B+NOP -> A'; observed 22 s to lock screen, 30 s autoswipe (from the Apple logo); 3 autoswipe attempts; driverkitd only | device run, 2026-10-22 |
| CI kernel boot | run `39648068844`, kernel `8a80855d...`, payload `2749bf1c...`, image `87dd4910...`; lock screen -> desktop; driverkitd + PosterBoard; no lsd/SpringBoard/backboardd | device run, 2026-10-22 |
| Board probe (P0, read-only) | 19 read-only commands over the USB console: watchdog not armed; I2C5 scan 4 ACKs (0x1a/0x34/0x4e/0x64); I2C5/6 idle high; MT6360 readable over I2C5 (LDO2/LDO3, device info, TCPC); clock gates not gated; GPIO 116/14/110/132 readable; six snapshots dumped; the volume-up key appears on GPIO 42; the two pwrap reads are blocked by the pwrap init gap | patchset `9f7b41cf...` (141 files); CI `41222632828`; kernel full `9c82ea75...`, exec `62a17d48...`; image `66352038...`; `config/0144.env` |

The ICL blocks, boot images, root images and logs are **not** in this
repository. Only their hashes and conclusions are recorded. Pre-boot image
hashes are fixed for the named files; post-boot root/ring/log hashes are
volatile and are not a contract (see `VERIFICATION.md` "Hash stability").

## 2026-11-07 state

| Item | Result | Evidence |
|---|---|---|
| Current line | 0180–0195 USB EP2: state machine, golden PHY, acknowledgements | patchset `a9cc0050...` (187); `config/0195.env` |
| Main/tag | `1e45453` / `v0.6.0`; line tag `usb-ep2-0194-2026-11-07` → `a9e24e2` | 2026-11-07 |
| Kernel | full `45ea1bc3...`, exec-data `6b22fc25...`; xnu `42301546006` + rerun `42302694315`; host-checks `42302515812`; main `42304310915` / `42304311052` | `config/0195.env`; workflow `xnu-0195` |
| Image | `x16-0195-ack.img` `fe009b89...`; payload `3a97d52b...`; built, not flashed | host build 2026-11-07 |
| Golden boot | 0194 `x16-0194-golden-srctrl.img` `1808e440...`; `golden acr5=0x40805000`; 14.1 s | device run 2026-11-07 |
| USB EP2 | 0189 stop/reset/start; SRCTRL=5 62-frame peak; board eye 6/3/2/13; short frames are log slices; big read no aggregation; pacing per-URB; transparent resume endpoint-only | `docs/en/13-usb-ep2-golden.md` |
| XactErr | USBD `0xC0000011`; ETW no CRC/toggle/STALL; USB2 analyser needed | 0180 ETW |
| Known limits | XactErr; 511 B framing; host-port drop under clear storms; no guarantee | 2026-11-07 |
| Rollback | 0194 `1808e440...`; 0189C `6eab7b69...`; TWRP archived | local archive |

## 2026-11-06 state

| Item | Result | Evidence |
|---|---|---|
| Current line | 0156-0179: P2 keys/USB hotplug/battery (0156-0174), P2 IRQ (0175), native EINT parent/child oneshot (0176-0179) | patchset `10b1e2e8...` (175 files); `config/0179.env` |
| Main/tag | `22cdb29` / `v0.5.0`; line tag `p2b-native-touch-2026-11-06` → `f6c5795` | 2026-11-06 |
| Kernel | full `2b008e52...`, exec-data `a4fb021e...`; CI `42114854911`; gate rerun `42115985782`; host-checks `42115991259` success | `config/0179.env`; workflow `xnu-0179` |
| Image | `x16-0179-touch-retry.img` `d438ba47...`; payload `72fc737c...`; `boot_a` 0179 | device run 2026-11-06 |
| Touch IRQ | EINT14 edge → EINT child controller → dedicated IOWorkLoop oneshot → SPI3/HID → `service_done` re-arm; `gt_thread` removed; commands on `IOCommandGate` | G1–G6; 0179 device run |
| Failure behavior | dirty frame dropped, line stays active; 8-failure streak → SPI FIFO reset + chip soft handshake (9 `no-ack`, `ok` path not proven); KPD independent | 0179 device run |
| Stress | first 10 min `isr 2381→6004`, `ok=5997`, `fail=7`; ~5 min `isr 8672→13282`, `ok=12866`, `fail +9`; 1–5 fingers; 0 panic/stuck/re-activation | 2026-11-06; device run |
| Known limits | G7/G8 and full 10 min repeat not run by decision; no ESD timer; `soft reset ok` unproven; battery UI 30 s; Type-C read-only; USB host/audio/Wi-Fi/BT/camera/GPU/RTC/sleep not implemented; single unit/host | decision 2026-11-06 |
| Rollback | 0178 `156f3d9f...`; 0177 `ecb5fe2c...`; 0176 `cc5c887c...`; 0155 `3b44c0e2...` | images external |

## 2026-11-02 state

| Item | Result | Evidence |
|---|---|---|
| Current line | 0155: P1 probe/pwrap (0146a/0147/0148), P2 keys/reboot/battery (0149/0150/0152/0152b/0154), P3 touch re-enable (0155) | patchset `da13b6df...` (151 files); `config/0155.env` |
| Kernel | full `491f2373...`, exec-data `2e98fd85...`; CI `41354317810`; gate rerun `41355922057` success | `config/0155.env`; workflow `xnu-0155` |
| Image | `x16-0155-a00dd751.img` `3b44c0e2...`; payload `a00dd751...`; `boot_a` 0155 | device run 2026-11-02 |
| Input | volume down KPD, power/volume up `TOPSTATUS 0x2a`; HID `0xe9/0xea/0x30`; zero PMIC writes; `0x910=0x0025` | 0150 device run; 0155 19/19 |
| Battery/charging | MT6360 read-only: OCV 4311 mV, CHG `0xa2` FULL, FOD `0x94` external, `external=1/full=1`; I2C5 shared IOLock; last-valid during probe; no PMIC/charger/rail writes | 0155 device run; `battery status`; `SWEET BATTERY: MT6360` |
| Touch | 0085 GT9916R BerlinD re-enabled with `sweetgt=1`; boot LDO section under the shared I2C5 lock; `BERLIN/9916R ready`; real HID down/up | 0155 device run; `SWEET GT`; 11+ HID lines |
| Probe/arbiter | 8/8 i2c5 take/line/release + battery; 19/19 probe; `i2c5 scan` 4 ack; `0x2a=0x000e`, `0x910=0x0025`; no panic | 0155 device run |
| Known limits | battery UI 30 s lag / 100→98 (P2.4); Type-C read-only; software fastboot/combo parked; USB replug needs reboot; USB host/audio/Wi-Fi/BT/camera/GPU/RTC/sleep not implemented; P3 target open | device run |

## 2026-11-01 state

| Item | Result | Evidence |
|---|---|---|
| Toolchain | The hosted image moved to `macos-15` and the Xcode version is a workflow input (default 16.0). xnu-8796 builds unchanged with it; the interface-compiler break the old recipe warned about did not reproduce | CI `41213328070` (140 files) and `41222632828` (141 files), both green; the 17 DriverKit interface files generated normally |
| P0 board probe (0144) | 19 read-only commands over the USB console; 17 returned board data, the two pwrap reads are blocked by the pwrap init gap | patchset `9f7b41cf...`; kernel full `9c82ea75...`, exec `62a17d48...`; image `66352038...`; `config/0144.env` |
| Enumeration (0145) | The attach budget gave the host 4 s per attempt and only three attempts, after which the device stopped attaching; widening the window to 12 s makes the host configure on the first try | patch `0145`; configured at 589 ms, 23 setups, no device-sent stall; device run 2026-11-01 |
| Stability | Ten-minute read-only idle: 15 samples, no panic, the console kept growing, the node stayed enumerated and repeated snapshots kept working | device run 2026-11-01; `config/0144.env` |
| Not scheduled | P1 pwrap minimal init, so the two pwrap reads stay empty; the endpoint-IN log spam and the per-session command budget are left for a later line | - |

## 2026-10-30 state

| Item | Result | Evidence |
|---|---|---|
| USB line (0143) | EP2 IN bulk MPS 512; 511-byte log frames; 64 GPD TX ring with at most 63 in flight; TX-ring reset on rearm; enumeration/config/HS green; host-side first-session XACT remains open (0-54 frames; EP0 may XACT; the device may drop) | patchset `f47f4c19...` (139 files); CI `41022192026`; kernel full `d2eae74d...`, exec `6fa65088...`; image `5b6b8411...`; `config/0143.env` |
| Host tooling | `tools/host/ruby_usb_host.py` (`status`/`cmd`/`watch`; EP0 read-only; one EP2 OUT command line; optional one-shot pnputil restart) | used for the 0143/0150/0151 runs; `docs/en/12-usb-host.md`, `docs/zh/12-usb-host.md` |
| Test conditions | Windows 11 NT 10.0.26300, AMD USB4 host, USB2 path on `1022:15b9`; tested with a USB4 Type-C/CC cable and a USB-A/A-C cable; the phone is bus-powered (no external AC adapter) | measured 2026-10-30; small samples; the XACT persists on both |
| Stability (0143) | A-port/A-C cable: 13/7/23 frames over three fresh boots, one device drop; ACR6 reads back `0x00100442` | author's host, 2026-10-30; numbers only |
| 0151 experiment | ACR6 SQTH=5 + bit28 (board HQA) rejected: enumeration failed with `setups=0` and three re-attach rounds | branch `usb-0151-sqth5`; not merged |

## 2026-10-29 state

| Item | Result | Evidence |
|---|---|---|
| Rescue root | LK ramdisk slot -> `md0`; PID 1 runs `/etc/rc` in-process; 8/8 rescue `/etc/rc` checks; USB `1209:0002` enumeration only (~35 s); EP2 XACT remains open | boot image `6795d9e4...` (rescue; B1 is `49a10e49...`); kernel exec `721e5daf...` |
| Main line (2026-10-29) | 0140 import + 0141 USB decouple; B1 image verified | squashed from `merge-ramdisk-usb-2026-10-29`; kernel input gated by run `40822689195` on the ramdisk line; pre-merge host-checks `40828162023` |
| USB line | 0131b probe write; EP2 host-side XACT remains open | `usb-0131b-probe-write` (merge `fb0577d`); kernel exec `06db2bb3...` |
| CI baseline | 82-file baseline from a private content-addressed mirror; public pin is manifest root `829d7598...`; fallback `ALLOW_PUBLIC_UPSTREAM=1` | `ci/baseline_manifest.py`; `config/0144.env` (current line), `config/0140.env`, `config/0131b.env` |
| Main | ramdisk + USB combined (squashed 2026-10-29) | see `docs/en/11-ci-baseline.md` |

## Build provenance (2026-11-06)

- Apple xnu: `xnu-8796.141.3` (`f625db25...`).
- Baseline: 82 files, manifest root `829d7598...`; private mirror, public
  fallback `ALLOW_PUBLIC_UPSTREAM=1`.
- 0179 line: patchset `10b1e2e8...` (175 files); kernel full `2b008e52...`,
  exec `a4fb021e...`; CI `42114854911`; gate rerun `42115985782`; host-checks
  `42115991259`; image `d438ba47...` (payload `72fc737c...`, `config/0179.env`);
  workflow `xnu-0179`.
- Build harness: `blacktop/darwin-xnu-build` @ `6639065`; macOS 13.5 xnu built
  on a `macos-15` runner with Xcode 16.0; `DEVELOPMENT` + `MACHINE_CONFIG=SWEET`,
  `-mcpu=cortex-a55`.

## Build provenance (2026-11-02)

- Apple xnu: `xnu-8796.141.3` (`f625db25...`).
- Baseline: 82 files, manifest root `829d7598...`; private mirror, public
  fallback `ALLOW_PUBLIC_UPSTREAM=1`.
- 0155 line: patchset `da13b6df...` (151 files); kernel full `491f2373...`,
  exec `2e98fd85...`; CI `41354317810`; gate rerun `41355922057`; image
  `3b44c0e2...` (`config/0155.env`); workflow `xnu-0155`.
- Build harness: `blacktop/darwin-xnu-build` @ `6639065`; macOS 13.5 xnu built
  on a `macos-15` runner with Xcode 16.0; `DEVELOPMENT` + `MACHINE_CONFIG=SWEET`,
  `-mcpu=cortex-a55`.
- The exec-data hash is the build gate; the earlier lines keep their hashes in
  the dated sections below.

## Build provenance (2026-11-01)

- Apple xnu: `xnu-8796.141.3` (`f625db25...`).
- Baseline: 82 files, manifest root `829d7598...`; private mirror, public
  fallback `ALLOW_PUBLIC_UPSTREAM=1`.
- 2026-11-01 line (0144 + 0145): patchset `9f7b41cf...` (141 files); kernel full
  `9c82ea75...`, core `34c8a93f...`, exec `62a17d48...`; CI `41222632828`;
  image `66352038...` (`config/0144.env`).
- Build harness: `blacktop/darwin-xnu-build` @ `6639065`; macOS 13.5 xnu
  built on a `macos-15` runner with Xcode 16.0; `DEVELOPMENT` +
  `MACHINE_CONFIG=SWEET`, `-mcpu=cortex-a55`.
- The exec-data hash is the build gate; the earlier lines keep their hashes
  in the dated sections below.

## Build provenance (2026-10-30)

- Apple xnu: `xnu-8796.141.3` (`f625db25...`).
- Baseline: 82 files, manifest root `829d7598...`; private mirror, public
  fallback `ALLOW_PUBLIC_UPSTREAM=1`.
- USB 0143: patchset `f47f4c19...` (139 files); kernel full `d2eae74d...`,
  core `c91060ab...`, exec `6fa65088...`; CI `41022192026`; image
  `5b6b8411...` (`config/0143.env`).
- USB 0142 (historical): patchset `d0c5ab5e...` (138 files); exec
  `99d98d80...`; CI `41015790742`; image `a31ee6dc...`.
- The host-side first-session XACT is not fixed by 0143; the exec-data hash
  is the build gate.

## Build provenance (2026-10-29)

- Apple xnu: `xnu-8796.141.3` (`f625db25...`).
- Baseline: 82 files, manifest root `829d7598...`; private mirror, public
  fallback `ALLOW_PUBLIC_UPSTREAM=1`.
- Main line (2026-10-29): patchset `27894e7b...` (137 files); kernel full `3acefe47...`,
  exec `721e5daf...`; kernel input gated by run `40822689195` on the ramdisk
  line; integration host-checks `40828162023`.
- USB branch: patchset `29449e32...` (135 files); kernel full `4e945ce6...`,
  exec `06db2bb3...`; CI `40824668335`.
- Rebuilds differ only in `__TEXT` metadata and the `__CTF` segment; every
  code/data segment and `__LINKEDIT` matches. The exec-data hash is the gate.
- No device flash for this change.

## Build provenance (0085)

- Baseline: `MakrSas/ios-topaz` @ `5095ac19dbdcf37b64b81fe443f4027ad51b84bf`.
- Recipe: `ci/prepare-baseline.sh`; canonical patchset
  `cf4008e309cfa566e3df968592a2d3f3224a9b3d0813d6054326115fecc0a03f`
  (88 files). The same canonical patchset built the booted 0085 kernel in the
  harness.
- 0010/0012 change: `ci/baseline-changes.patch`, SHA256 `1edb6633...`.
- Historical origin: harness commit `8716a06`.
- Build harness: `blacktop/darwin-xnu-build` @ `6639065`; macOS 13.5 / Xcode
  15.0.1 on a `macos-14` runner; `DEVELOPMENT` + `MACHINE_CONFIG=SWEET`,
  `-mcpu=cortex-a55`.
- Booted kernel SHA256 `9eb9acac...`; exec-data hash `e4823afb...` (the
  artifact-level gate); boot image `ace60d16...`.
- Workflow: `.github/workflows/xnu.yml`. It runs the recipe, enforces the
  patchset hash, and gates the built kernel's exec-data hash against
  `e4823afb...`; see `ci/README.md`.
- 2026-10-22 CI run `39694456200` on branch `touch-0085` (`042ec31`) succeeded:
  kernel full `904e10df...`, exec-data `e4823afb...` (matches the booted
  kernel), CI image `54d1b306...` (packed locally, not flashed).
- 2026-10-22 main CI run `39696625623` (`53dc3a9`) succeeded: kernel full
  `00cb6cc8...`, exec-data `e4823afb...` (matches), per-segment
  `__TEXT_EXEC`/`__DATA_CONST` match. Packed to `61f9d24e...`, flashed to
  `boot_a`, and **booted on the author's unit; real touch works**.

### Previous milestone (0084)

- Patchset `de1824c2...` (87 files); 0084 kernel `b38fca5f...` (reference) and
  `8a80855d...` (2026-10-22 CI run `39648068844`); image `94c639d1...`.
- The 0084 synthetic autoswipe reached the home screen; real touch was not
  implemented yet.
- **Device regression:** the 0084 first boot and CI kernel boot were run on the
  author's unit on 2026-10-22; a second unit / clean-room is still open.
  Device-baseline hashes are intentionally not published.

## Reproducibility guarantee

The success path now has **one-unit device evidence** (B+NOP first boot ->
A', the CI kernel boot, the 0155 run and the 0179 P2b line) plus the
documented recipe. It is not an independently reproduced second-unit or
clean-room guarantee; G7/G8 and a full 10 min repeat were not run. Pre-boot
image hashes are fixed for the named files; post-boot root/ring/log hashes are
volatile. See [`GUARANTEE.md`](GUARANTEE.md) and the "Hash stability" section
of `VERIFICATION.md`.

## Not working

- Wi-Fi, Bluetooth, cellular, audio, camera, GPU, RTC; sleep/wake; USB host/OTG;
  charger control/OTG; Type-C role.
- Battery/charging is read-only; the UI polls every 30 s (P2.4: 100→98 on
  unplug).
- P2b: no ESD timer (a silent stuck panel needs a reboot); `soft reset ok` is
  unproven; G7/G8 and a full 10 min repeat were not run.
- Software fastboot and the volume-down+power combo are parked; USB hotplug
  repeatability was 7/10 `cfg=1` and the host `GONE` signal is unreliable.
- MobileGestalt cache is absent; the ICL NOP is a bypass, not a fix.
- The original (unpatched) ICL block has not been regression-tested after the
  first-boot state was created.
- PosterBoard/wallpaper and some WidgetKit surfaces are incomplete.

## Verification levels

- **host-verified**: commands and tools run on the author's PC against local
  files; see `VERIFICATION.md`.
- **device-verified (2026-11-06)**: 0179 (patchset `10b1e2e8...`; exec
  `a4fb021e...`) booted on the author's unit: native EINT14 touch, G1–G6,
  first 10 min + ~5 min stress, 1–5-finger HID, no panic/stuck/re-activation;
  the 8-failure soft-reset branch logged `no-ack` (accepted boundary). G7/G8
  and the full 10 min repeat were cancelled by decision.
- **device-verified (2026-11-02)**: 0155 (patchset `da13b6df...`; exec
  `2e98fd85...`) booted on the author's unit: GT9916R touch, volume/power keys,
  battery 4311 mV `external=1/full=1`, 8/8 I2C5 arbiter, 19/19 probe, no panic;
  known P2.4 battery UI latency and Type-C read-only.
- **device-verified (2026-10-22)**: B+NOP first boot -> A', the CI kernel boot,
  and the real-touch 0085 boot were observed on the author's unit. The 0085
  sweetlog shows `BERLIN/9916R`, 206 down / 206 up records, 40 finger-1 and
  84 edge records. `SweetHIDTouch` appends both active contacts to one
  digitizer collection; a user-visible pinch was not separately instrumented. Post-boot hashes (live root, ring, logs) are volatile
  observations, not fixed pins.
- **not verified**: everything else, including a from-scratch public
  reproduction on a different ruby unit, a second-unit boot, and the strict
  pinned payload rebuild (the CI test used ref `33852e3`).
