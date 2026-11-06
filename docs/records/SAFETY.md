# Safety

Read this before flashing anything.

- **Experimental.** No warranty. The device may become unbootable.
- **Data.** Assume `userdata` will be lost. Back up `boot`, `dtbo`, `vbmeta`,
  `persist`, `modemst1/2`, `fsg`, `fsc` and anything you cannot recreate.
- **Bootloader.** An unlocked bootloader is required. Do not flash `preloader`,
  `lk`, `persist`, `nvram` or `nvdata`.
- **Recovery.** `ruby` has no recovery partition and its LK has no `boot:`
  command; TWRP must be flashed to `boot_a`. Keep a known-good boot image and a
  TWRP image available before experimenting.
- **Raw block tools.** `blkpatch` writes raw blocks. Run it through
  `twrp-guard.sh`, pass an explicit block device, back up the target blocks
  first, and verify with `blkdiff` afterwards.
- **Security.** AMFI, sandbox and code signing are disabled or bypassed in this
  bring-up. Do not store personal data on the iOS side.
- **Legal.** Apple's userland and firmware are not included. Obtain your own
  IPSW and comply with Apple's terms. This is research, not a product.
- **No Apple services.** The bring-up does not contact Apple activation or
  identity servers.
