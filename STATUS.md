# Status

As of **2026-10-22**. This is a snapshot of verified results, not a live device
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
| Patch checks | 0084/0083/0081 apply to the pre-0084 build tree; 0080/0082 are already applied; 0085 applies after 0084 and built successfully | host-side `git apply --check`; CI run `39694456200` |
| ICL tool | original block -> patched block reproduces `4a489542...` | host-side round-trip, 2026-10-21 |
| Host pipeline | payload `50701e81...`; deterministic rebuild `a0ce0fe1...`; layout PASS vs 0084 | host-only, 2026-10-21; no root/phone |
| Host checks | strict host bundle PASS; config-mode layout PASS (11 checks); Linux host CI green before the final docs/template-only amendment | host-only, 2026-10-21 |
| Root state audit | A `e698339d...` (post-boot22), B `985c30...` (pre-boot22), C `34c2882d...` (clean base), A' `55e2ab2c...` (first-boot snapshot) | read-only audit, 2026-10-22 |
| First boot from B+NOP | B+NOP -> A'; observed 22 s to lock screen, 30 s autoswipe (from the Apple logo); 3 autoswipe attempts; driverkitd only | device run, 2026-10-22 |
| CI kernel boot | run `39648068844`, kernel `8a80855d...`, payload `2749bf1c...`, image `87dd4910...`; lock screen -> desktop; driverkitd + PosterBoard; no lsd/SpringBoard/backboardd | device run, 2026-10-22 |

The ICL blocks, boot images, root images and logs are **not** in this
repository. Only their hashes and conclusions are recorded. Pre-boot image
hashes are fixed for the named files; post-boot root/ring/log hashes are
volatile and are not a contract (see `VERIFICATION.md` "Hash stability").

## 2026-10-29 state

| Item | Result | Evidence |
|---|---|---|
| Rescue root | LK ramdisk slot -> `md0`; PID 1 runs `/etc/rc` in-process; 8/8 rescue `/etc/rc` checks; USB `1209:0002` enumeration only (~35 s); EP2 XACT remains open | boot image `6795d9e4...` (rescue; B1 is `49a10e49...`); kernel exec `721e5daf...` |
| Main line (2026-10-29) | 0140 import + 0141 USB decouple; B1 image verified | squashed from `merge-ramdisk-usb-2026-10-29`; kernel input gated by run `40822689195` on the ramdisk line; pre-merge host-checks `40828162023` |
| USB line | 0131b probe write; EP2 host-side XACT remains open | `usb-0131b-probe-write` (merge `fb0577d`); kernel exec `06db2bb3...` |
| CI baseline | 82-file baseline from a private content-addressed mirror; public pin is manifest root `829d7598...`; fallback `ALLOW_PUBLIC_UPSTREAM=1` | `ci/baseline_manifest.py`; `config/0140.env`, `config/0131b.env` |
| Main | ramdisk + USB combined (squashed 2026-10-29) | see `docs/en/11-ci-baseline.md` |

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
A', and the CI kernel boot) plus the documented recipe. It is not an
independently reproduced second-unit or clean-room guarantee. Pre-boot image
hashes are fixed for the named files; post-boot root/ring/log hashes are
volatile. See [`GUARANTEE.md`](GUARANTEE.md) and the "Hash stability" section
of `VERIFICATION.md`.

## Not working

- Hardware buttons.
- USB, Wi-Fi, Bluetooth, cellular, audio, camera, GPU, RTC.
- MobileGestalt cache is absent; the ICL NOP is a bypass, not a fix.
- The original (unpatched) ICL block has not been regression-tested after the
  first-boot state was created.
- PosterBoard/wallpaper and some WidgetKit surfaces are incomplete.

## Verification levels

- **host-verified**: commands and tools run on the author's PC against local
  files; see `VERIFICATION.md`.
- **device-verified (2026-10-22)**: B+NOP first boot -> A', the CI kernel boot,
  and the real-touch 0085 boot were observed on the author's unit. The 0085
  sweetlog shows `BERLIN/9916R`, 206 down / 206 up records, 40 finger-1 and
  84 edge records. `SweetHIDTouch` appends both active contacts to one
  digitizer collection; a user-visible pinch was not separately instrumented. Post-boot hashes (live root, ring, logs) are volatile
  observations, not fixed pins.
- **not verified**: everything else, including a from-scratch public
  reproduction on a different ruby unit, a second-unit boot, and the strict
  pinned payload rebuild (the CI test used ref `33852e3`).
