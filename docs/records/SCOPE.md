# Scope

## Main line

- XNU 8796 plus an iPhone X iOS 16.7.16 userland on `ruby` / MT6877.
- Boot chain, UFS/HFS+ root, display, launchd/SpringBoard and HID.
- Reproducible patches, offline image tools and host-side verification.

## Appendix

- The dual-boot layout (shrink `userdata`, create `iosroot`) is a **method
  note**, not the default path and not automated. See
  [`../en/appendix-dualboot.md`](../en/appendix-dualboot.md) (or the
  [Chinese version](../zh/appendix-dualboot.md)).

## Default path and data risk

The default upstream-compatible path writes the iOS root into `userdata` (or a
dedicated partition) and can erase Android data. Assume data loss and back up
first. The dual-boot method avoids the initial erase but edits the GPT and
uses raw `dd`; it is not "safe" and is not recommended for most users.

## Reproducibility guarantee

Only the success path (boot to the lock screen, synthetic swipe to the home
screen) is covered, and it is a **documented, theoretical guarantee**: same
device baseline, same root/boot artifact hashes, same boot args, documented
steps. It is not an independently reproduced device guarantee. Detailed test
guarantees are deferred due to time and effort; failed routes are historical
evidence, not supported paths. See [`GUARANTEE.md`](GUARANTEE.md).

## Not in scope

- Apple firmware, IPSW/DMG, iOS root images, dyld shared caches, userland
  binaries.
- Device dumps, serials, IMEI/MAC, Apple account data, diff data, full logs.
- Photos and videos (the `media/` directory is reserved).
- One-off agent scripts and device-specific automation.
- A daily-driver OS, Android modification, Apple services or activation
  against Apple servers.
- A one-click installer or an automated repartition tool.

## Rules for contributions

- No firmware, images, dumps or personal data.
- Every hardware number must be traceable to a device tree, a measurement or a
  cited upstream source.
- Distinguish measured, inferred and historical claims.
- Offline tools must default to dry-run and must validate input hashes before
  writing.
