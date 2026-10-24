# Patches

These are diffs against XNU 8796 as used by the `ios-topaz` baseline. They are
not standalone source. Apply the upstream series first, then these in numeric
order.

| Patch | State | Target | Purpose |
|---|---|---|---|
| `0080-ruby-ufs.patch` | current | `bsd/dev/sweet_ufs.c` | UFS root on LUN 2, GPT header at 512 / entries 1024, `iosroot` partition |
| `historical/0081-ruby-swap-debug.patch` | historical | `iokit/Kernel/arm/SweetFramebuffer.cpp` | framebuffer VA flush / debug markers |
| `historical/0082-ruby-wifi-stub.patch` | historical | `iokit/conf/files.arm64`, `iokit/KernelConfigTables.cpp`, `iokit/Kernel/arm/SweetNetwork.cpp` | minimal `IONetworkController` stub for the MobileGestalt wait |
| `historical/0083-ruby-iokit-match-trace.patch` | historical | `iokit/Kernel/IOService.cpp` | IOKit match/notification trace |
| `0084-ruby-autoswipe.patch` | historical | `iokit/Kernel/arm/hid/SweetHID.cpp` | boot-arg synthetic swipe to unlock the lock screen (previous milestone) |
| `0085-ruby-goodix-spi.patch` | current | `bsd/dev/sweet_goodix_spi.c`, `bsd/conf/files`, `bsd/dev/sweet_ufs.c` | GT9916R BerlinD over GPIO bit-bang SPI3: MT6360 LDO3/LDO2 1.8/3.3 V, reset/IOVDD, dev_confirm/version, touch-frame poll into `sweet_hid_touch()` |
| `0086-ruby-usb-p0.patch` | current | `bsd/dev/ruby_usb.c`, `bsd/conf/files`, `bsd/dev/sweet_ufs.c` | MTU3 USB2 device P0: IPPC power/reset, U2/U3 PHY, IDDIG, D+ pull-up, PS5169 GPIO121, force-VBUS and soft-connect; `rubyusb=1`, no EP0/IRQ/DMA |
| `0087-ruby-usb-p2.patch` | WIP | `bsd/dev/ruby_usb.c` | P2 polling EP0 enumeration: raw setup capture, device/config/string descriptors, SET_ADDRESS/SET_CONFIGURATION, trace ring; no IRQ/DMA |
| `0088-ruby-handoff-dump.patch` | WIP | `bsd/dev/ruby_usb.c` | `rubydump=1`: dump PE_state/DT header and IPPC/MAC/PHY registers to SWEETLOG at probe entry (stage0) and after the EP0 window (stage1) |
| `0089-ruby-ep0-timing.patch` | WIP | `bsd/dev/ruby_usb.c` | EP0 data-IN: wait ~100 us and for `EP0_FIFOFULL` clear before `DATAEND` (P9-proven timing) |
| `0090-ruby-devspeed-hs.patch` | WIP | `bsd/dev/ruby_usb.c` | keep `DEVICE_CONF` speed=3 (HS) at probe init instead of clearing it to 0 |
| `0091-ruby-devconf-offset.patch` | WIP | `bsd/dev/ruby_usb.c` | fix `DEVICE_CONF` offset `0x1800` -> `0x0800` (SET_ADDRESS); revert 0090 to vendor value 0 |
| `0092-ruby-config-endpoints.patch` | WIP | `bsd/dev/ruby_usb.c` | vendor-specific interface (class 0xFF) with EP2 OUT/IN bulk; 32-byte config so SET_CONFIGURATION is issued |
| `0093-ruby-poll-pid.patch` | WIP | `bsd/dev/ruby_usb.c` | EP0 poll 1 ms -> 100 us; PID 0x0001 -> 0x0002 so WinUSB selects the configuration |

`0080` and `0085` are the changes used by the current real-touch boot. `0086`
adds the USB P0 probe and is inert unless `rubyusb=1`; it does not use the
topaz `sweet_usb.c` DWC3 driver. `0084` is the previous synthetic-swipe
milestone and is not required when real touch is enabled. `0081`-`0083` are
kept as evidence of the path; `0082`/`0083` were superseded by the ICL NOP
bypass. Applying a historical patch is not required for a new build.

Check before applying:

```sh
git apply --check patches/0086-ruby-usb-p0.patch
```

The patches modify Apple's XNU and remain under APSL 2.0; see `../NOTICE`.
