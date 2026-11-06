# Root recipe

**English** · [中文](../zh/root-recipe.md)

No root image is included. The success root (A) is a **pulled v14 root** with
the boot22 first-boot state and the ICL block patch; its artifact hash is
`e698339d...`. The pre-boot22 pulled+seeded root (B) is `985c30...`; the clean
mkiosroot base (C) is `34c2882d...`. The boot22 diff (62,490 4K blocks,
external) maps B -> A. This page is a recipe, not an installer, and it does
not automate the 16 GiB root.

## What the root is

- An HFS+ image of the iPhone X iOS 16.7.16 (20H392) userland.
- A: post-boot22 success snapshot, with the ICL NOP and the first-boot state.
- B: pre-boot22 pulled+seeded root, with the ICL original block; the boot22
  diff maps B -> A.
- C: clean mkiosroot + tweaks base; C alone may stop at LS/MG; the device
  first boot/seed is still needed.
- A': the first-boot snapshot from B+NOP; one run, not stable across first
  boots. A new first boot is a new state (A'').
- The v14 lineage: a pulled `/private/var` + fsck + `DataMigration.plist`
  (`LastSystemVersion=20H392`), plus the transport tweaks.
- The boot22 diff: 62,490 changed 4K blocks (244 MiB), including the first-boot
  state; the diff data is not in this repo.
- The ICL 4K block: `2438140`, original `ae317804...`, patched `4a489542...`.
- The exact state matters. A fresh IPSW root is a different path and may stop
  at LaunchServices/MobileGestalt before the UI.

## Inputs

- An iPhone X iOS 16.7.16 (20H392) IPSW and an HFS+ image toolchain.
- A pulled root (preferred) or a fresh IPSW root plus a device first-boot run.
- The exact v14 tweaks: Setup skip, `BKNoWatchdogs`, `HAL.disabled`,
  CommCenter removal, `data_ark`, ByHost migration preferences, containers,
  and the MediaToolbox recorder-off setting.
- TWRP A12 and a known-good `boot_a` for offline writes.

## Outline

1. Extract the D22AP IPSW; create a 16 GiB HFS+ image (17 GiB `iosroot` in the
   dual-boot example; the default path may use a dedicated partition).
2. Copy the userland; apply the v14 tweaks and seed the containers/ByHost/
   `data_ark`.
3. First boot on the device to create the first-boot state; freeze the root
   image. For the success state, start from B with the ICL NOP applied; the
   resulting A' is not expected to hash-match A. This step is device-side and
   is not automated here.
4. Patch the ICL 4K block with `tools/image/icl_nop.py`; verify the original
   and patched block hashes.
5. Write the frozen root to `iosroot` with TWRP raw `dd`; verify the SHA.
6. Keep the original root image and the ICL original block for rollback.

## Limits

- No 16 GiB root image or diff data is in this repo.
- A, B and C are external states. B and C full images are not retained; A is
  the success snapshot; A' is a first-boot snapshot.
- The root image is not distributable; users must supply it.
- Pre-boot image hashes are fixed; post-boot live-root/ring/log hashes are
  volatile. See the "Hash stability" section of `docs/records/GUARANTEE.md`.
- The exact first-boot state may require a device run; a host-only recipe
  cannot recreate the pulled phone state.
- No device regression tests were run for this packaging.
