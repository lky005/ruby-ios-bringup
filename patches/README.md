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
| `0094-ruby-ep0-thread.patch` | WIP | `bsd/dev/ruby_usb.c` | leave the EP0 window 200 ms after SET_CONFIGURATION; 1 ms EP0 kernel thread keeps servicing control requests after boot |
| `0095-ruby-ep2-log.patch` | WIP | `bsd/dev/ruby_usb.c` | EP2 IN QMU log pipe: 4-GPD ring, PA translation + 36-bit high nibble, `dc civac`, checksum, 64 B SWEETLOG increments every ~100 ms |
| `0096-ruby-ep2-ring-guard.patch` | WIP | `bsd/dev/ruby_usb.c` | static ring/log PA, HWO drop instead of reusing a live GPD, `QISAR1` ack-only, 16 B per-packet diagnostic header |
| `0097-ruby-ep2-serialize.patch` | WIP | `bsd/dev/ruby_usb.c` | one GPD in flight: the TX-done bit releases the slot, nothing else clears the busy flag |
| `0098-ruby-ep2-state.patch` | WIP | `bsd/dev/ruby_usb.c` | vendor IN `0xC0/0x21` returns the live EP2/QMU state, `SENTSTALL` poll, `CLEAR_FEATURE` recovery, P9 kick order |
| `0099-ruby-ep2-nozlp.patch` | WIP | `bsd/dev/ruby_usb.c` | disable the EP2 TX ZLP (a 64 B frame is already `wMaxPacketSize`) |
| `0100-ruby-ep2-recover.patch` | WIP | `bsd/dev/ruby_usb.c` | P9-style endpoint recovery (W1C stall + `EP_RST`), busy watchdog, error telemetry in the vendor state |
| `0101-ruby-ep0-nodataend.patch` | WIP | `bsd/dev/ruby_usb.c` | EP0 never writes `DATAEND` into a full FIFO: it stalls instead, so a missed transfer cannot wedge EP0 |
| `0102-ruby-ep2-slot0.patch` | WIP | `bsd/dev/ruby_usb.c` | EP2 TX slot 0 (one 512 B FIFO segment), 0.5 s busy watchdog, FIFO capacity in the vendor state |
| `0103-ruby-ep0-reset.patch` | WIP | `bsd/dev/ruby_usb.c` | EP0 setup capture waits for a short packet instead of stalling; the host bus reset (MAC2 common-USB status) is polled and recovered (address back to 0, EP0 re-armed, EP2/QMU stopped); EP0 is armed before the pull-up; a debounced VBUS sense re-arms the device after an unplug |
| `0104-ruby-ep0-p9-parity.patch` | WIP | `bsd/dev/ruby_usb.c` | EP0 writes `DATAEND` even when the TX FIFO is still full instead of stalling (the P9 probe never stalled there, and the stall made the host abandon the enumeration); the bus-reset recovery drains the EP0 FIFO; every trace entry and log line carries a millisecond stamp so the device timeline can be anchored on the host connect event |
| `0105-ruby-ep0-ack-fifo-drain.patch` | WIP | `bsd/dev/ruby_usb.c` | the EP0 status stage waits for the TX FIFO to drain before it is written: the host sends SET_ADDRESS as soon as it has the device descriptor, and ACKing into a full FIFO made the xHCI Address Device command fail with CompletionCode 4, so the host reset the port and enumerated again |
| `0106-ruby-ep0-ack-fast-drain.patch` | WIP | `bsd/dev/ruby_usb.c` | the same drain wait, shortened from 50 ms to 2 ms: the long wait made the hub path enumerate but broke the direct path, where the controller's response window is tighter; the time actually spent is reported in the trace |
| `0107-ruby-ep0-p9-latency.patch` | WIP | `bsd/dev/ruby_usb.c` | EP0 response latency back to the bare-metal P9 semantics: the data stage waits 2 ms (not 300 ms) for the TX FIFO before writing `DATAEND`, and the status stage is written without any wait, like the vendor driver and the P9 probe |
| `0108-ruby-ep2-frame63.patch` | WIP | `bsd/dev/ruby_usb.c` | EP2 log frames are 63 bytes, one below `wMaxPacketSize`: the verified P9 TX path only sent short packets, while 64-byte frames are an exact multiple that never produced a QMU TX done |
| `0109-ruby-ep2-slot2.patch` | WIP | `bsd/dev/ruby_usb.c` | EP2 TX slot back to 2, the value the verified P9 probe uses: 0102 changed the bulk endpoint to slot 0, the only endpoint-configuration difference left after the 63-byte frame test showed that frame length was not the cause |
| `0110-ruby-ep2-queue.patch` | WIP | `bsd/dev/ruby_usb.c` | keep the EP2 QMU ring populated like the vendor driver: one buffer per GPD, one free sentinel slot, refill on TX done from the 1 ms thread, and walk completed GPDs with the current-GPD address plus HWO; a read-only vendor request exposes the queue diagnostics |
| `0111-ruby-ep2-resume.patch` | WIP | `bsd/dev/ruby_usb.c` | the EP2 timeout only resumes the QMU every two seconds like the bare-metal P9 path instead of pulsing `EP_RST`: resetting the endpoint while the host was not reading flushed the FIFO repeatedly and reordered the stream; the timeout is armed only after the first TX done, so a bulk IN queue stays silent until the host has issued an IN token |
| `0112-ruby-ep2-rx.patch` | WIP | `bsd/dev/ruby_usb.c` | add EP2 bulk OUT Stage A: 16 pre-armed RX GPDs with per-slot 64-byte buffers, the vendor RX GPD layout and RQCPR/HWO completion, slot 2/FIFO and ZLP configuration, and a read-only `0xC0/0x23` RX counter/CRC diagnostic; `QISAR1` is now cleared per direction so RX errors are not swallowed by the TX path |
| `0112b-ruby-ep2-rx-diag.patch` | WIP | `bsd/dev/ruby_usb.c` | RX diagnostics only: a raw current/prev/next GPD request (`0xC0/0x24`), an RX reset for clean per-length tests (`0xC0/0x26`), CLEAR_FEATURE for EP2 OUT, RX2CSR0 stall and ZLP-error visibility; no buffer, GPD-layout, queue or TX change |

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
