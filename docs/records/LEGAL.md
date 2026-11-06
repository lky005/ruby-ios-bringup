# Legal and risk notice

**English** · [中文](LEGAL.zh.md)

**This is not legal advice.** Laws differ by jurisdiction. Consult a qualified
lawyer before public redistribution or commercial use.

## What this repository is

A research and interoperability record for running an open-source kernel and a
user-supplied iOS userland on a device the user owns. It is provided for
academic research and interoperability study only, not as a product, and comes
with no warranty. It is not affiliated with Apple, Xiaomi, MediaTek, the
upstream projects, or their affiliates.

## No Apple binaries

The repository does **not** include Apple firmware, IPSW/DMG files, iOS root
images, dyld shared caches, or Apple userland binaries. Addresses, offsets and
short disassembly windows are recorded as factual observations. Users must
obtain any Apple material themselves and comply with Apple's terms.

## Patches and upstream licenses

- The patches in `patches/` modify Apple's XNU and remain under APSL 2.0.
- `ios-sweet` and `ios-topaz` had **no license file** at the pinned commits.
  No upstream tree is copied into this repository and no full delta is
  published. The recipe fetches the upstream tree and applies
  `ci/baseline-changes.patch` (a small 0010/0012 change) plus this project's
  patches. CI fetches the baseline patch set from a private content-addressed
  mirror; only its manifest root and the disclosed 0010/0012 change are
  published. No complete upstream patch file is redistributed. Before public
  redistribution, obtain permission from the upstream authors or keep the
  repository private.
- TWRP and Magisk are GPL-licensed; their images are not included.

## Reverse engineering and circumvention

The repository documents a userland `InstalledContentLibrary` NOP, disabled
AMFI/sandbox/code signing, and shared-cache offsets used during research.
Reverse-engineering and anti-circumvention rules vary widely (for example,
DMCA §1201 in the United States and local laws elsewhere).

The project does **not** provide Apple activation, DRM, or account bypasses,
and does not contact Apple servers. Do not use it for piracy, unauthorized
access, or bypassing another person's device protections. If you plan to
publish or commercialize it, obtain legal review first.

## Device risk

Unlocking, flashing, repartitioning, and raw block writes can void warranties,
erase data, or brick a device. There is no warranty. Assume data loss.

## Trademarks

Apple, iPhone, iOS, Xiaomi, Redmi, MediaTek, and other names are trademarks of
their owners. They are used here only for identification and compatibility
description.

## Privacy

The repository contains no serial numbers, IMEI, MAC addresses, Apple account
data, or personal paths. Do not add them. Media must be sanitized according to
`media/CAPTURE.md` before it is committed.
