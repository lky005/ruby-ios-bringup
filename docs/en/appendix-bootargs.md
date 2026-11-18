# Appendix — boot arguments and image packaging parameters

**English** · [中文](../zh/appendix-bootargs.md)

> Status tags follow the [repository README](../../README.md). Defaults below
> were read from the 0334 sources (`ruby_usb_probe()` and friends); the
> baseline cmdline is 587 B, the limit is 607 B.

## Recommended cmdline presets (copy-paste)

All three strings below are full, ready-to-use `--cmdline` values. They were
taken from the verified 0332i/0334 builds; the kernel does not change its
defaults.

**1) Default path (587 B, `rubywinusb=4`, hotplug off):**

```text
debug=0xc serial=3 cpus=6 keepsyms=1 -noprogress rd=ufsroot0 ufsroot=iosroot ufsrw=1 rootrw=1 sweethw=0 ufslun=2 launchd_unsecure_cache=1 unentitled_ios_sim_launch=1 ignition_level=1 wdt=-1 wdt_test=no_user_checkin sweetfb_noconsole=1 sweetfb_hz=30 rubyusb=1 ufslogsecs=1 rubyprobe=1 rubyep2log=0 rubypwrap=1 rubkeys=1 rubybatt=1 rubyeint=1 rubymt6360=1 rubyeintirq=1 rubykpdirq=1 rubyeintb1=1 rubyusbirq=1 rubyqmuirq=1 rubypad=1 rubydmauc=1 rubyusbcmd=1 ruby_rxskip=1 ruby_txreset=0 ruby_clr01=1 rubyreboot=1 ruby_zlp=0 ruby_enum=0 ruby_echo=1 ruby_iddump=1 rubywinusb=4 rubysetupdump=1
```

**2) Recommended open-box set (605 B): the same string plus
`rubyusb_hotplug=1`, so WinUSB binding and port events are both on:**

```text
debug=0xc serial=3 cpus=6 keepsyms=1 -noprogress rd=ufsroot0 ufsroot=iosroot ufsrw=1 rootrw=1 sweethw=0 ufslun=2 launchd_unsecure_cache=1 unentitled_ios_sim_launch=1 ignition_level=1 wdt=-1 wdt_test=no_user_checkin sweetfb_noconsole=1 sweetfb_hz=30 rubyusb=1 ufslogsecs=1 rubyprobe=1 rubyep2log=0 rubypwrap=1 rubkeys=1 rubybatt=1 rubyeint=1 rubymt6360=1 rubyeintirq=1 rubykpdirq=1 rubyeintb1=1 rubyusbirq=1 rubyqmuirq=1 rubypad=1 rubydmauc=1 rubyusbcmd=1 ruby_rxskip=1 ruby_txreset=0 ruby_clr01=1 rubyreboot=1 ruby_zlp=0 ruby_enum=0 ruby_echo=1 ruby_iddump=1 rubywinusb=4 rubysetupdump=1 rubyusb_hotplug=1
```

**3) Test-channel lite image (585 B): default set with `rubyep_test=1` and
`ruby_iddump=1` dropped; used for the 0331 matrix and the 0334 T2 batch:**

```text
debug=0xc serial=3 cpus=6 keepsyms=1 -noprogress rd=ufsroot0 ufsroot=iosroot ufsrw=1 rootrw=1 sweethw=0 ufslun=2 launchd_unsecure_cache=1 unentitled_ios_sim_launch=1 ignition_level=1 wdt=-1 wdt_test=no_user_checkin sweetfb_noconsole=1 sweetfb_hz=30 rubyusb=1 ufslogsecs=1 rubyprobe=1 rubyep2log=0 rubypwrap=1 rubkeys=1 rubybatt=1 rubyeint=1 rubymt6360=1 rubyeintirq=1 rubykpdirq=1 rubyeintb1=1 rubyusbirq=1 rubyqmuirq=1 rubypad=1 rubydmauc=1 rubyusbcmd=1 ruby_rxskip=1 ruby_txreset=0 ruby_clr01=1 rubyreboot=1 ruby_zlp=0 ruby_enum=0 ruby_echo=1 ruby_iddump=1 rubywinusb=4 rubyep_test=1
```

Notes:

- `rubyusb_susp=1` is another 17 B; adding it to preset 2 reaches 622 B, over
  the 607 B limit. Drop a probe argument if you need it.
- Preset 2 enables port events; the 0334 default A/B evidence used hotplug
  off. Hotplug-on evidence is the 0333 line (10/10 re-enumeration).
- `rubywinusb=4` is MS OS 1.0 WCID with the bcdDevice bump (`0x0212`) that
  makes Windows re-probe `0xEE`. Do not remove it if you want WinUSB to bind.

## Stock and board arguments in the presets (18)

| Argument | Purpose |
|---|---|
| `debug=0xc`, `serial=3`, `cpus=6`, `keepsyms=1`, `-noprogress` | boot/serial/symbol debug plumbing |
| `rd=ufsroot0 ufsroot=iosroot ufsrw=1 rootrw=1 sweethw=0 ufslun=2` | root device: UFS LUN 2, read/write HFS+ |
| `launchd_unsecure_cache=1 unentitled_ios_sim_launch=1 ignition_level=1` | userland bring-up gates |
| `wdt=-1 wdt_test=no_user_checkin` | watchdog off for bring-up |
| `sweetfb_noconsole=1 sweetfb_hz=30` | framebuffer console off, 30 Hz |
| `ufslogsecs=1` | UFS log timing |

## Project arguments in the presets (26)

| Argument | Default | Purpose |
|---|---|---|
| `rubyusb=1` | 0 | master USB enable; every USB path below needs it |
| `rubyprobe=1` | 0 | vendor probe channel |
| `rubyep2log=0` | -1 (ACM default) | EP2 log stream; 0 off, 1 on |
| `rubypwrap=1`, `rubybatt=1`, `rubymt6360=1` | 0 | board: pwrap, battery, MT6360 |
| `rubkeys=1`, `rubyeint=1`, `rubyeintirq=1`, `rubykpdirq=1`, `rubyeintb1=1` | 0 | keys and EINT/IRQ path |
| `rubyusbirq=1`, `rubyqmuirq=1` | 0 | USB IRQ mode and QMU done IRQs |
| `rubypad=1` | 0 | clock/pad tuning variant |
| `rubydmauc=1` | 0 | uncached DMA ring alias |
| `rubyusbcmd=1` | 0 | EP0 command runner + ACM command mode |
| `ruby_rxskip=1` | 0 | skip the RX path when only TX is exercised |
| `ruby_txreset=0` | 0 | TX reset recovery on stall |
| `ruby_clr01=1` | 0 | CLEAR_FEATURE(0x01) parity handling |
| `rubyreboot=1` | 0 | reboot-to-fastboot path |
| `ruby_zlp=0` | 0 | ZLP tail on MPS-aligned transfers |
| `ruby_enum=0` | -1 (ACM default) | descriptor profile 0/1/2 |
| `ruby_echo=1` | -1 | raw echo on EP1 |
| `ruby_iddump=1` | 0 | identity property dump at boot |
| `rubywinusb=4` | 0 | MS OS 1.0 binding (0 off, 1–3 MS OS 2.0, 4 MS OS 1.0) |
| `rubysetupdump=1` | 0 | SETUP packet trace |

## USB driver arguments not in the presets (grouped)

Defaults are the compiled defaults; change one at a time. The full parse
block is `ruby_usb_probe()` in `bsd/dev/ruby_usb.c`.

### Queue geometry

| Argument | Default | Purpose |
|---|---|---|
| `ruby_txgpd` | 512 | TX bytes per GPD (64–16384, 512 multiples) |
| `ruby_txgpd_num` | 64 | TX GPD slots in the ring (8–64) |
| `ruby_rxgpd_num` | 16 | RX GPD slots (4–16) |
| `ruby_inflight` | 16 | TX GPDs in flight (1..ring−1) |
| `ruby_rxbuf` | 512 | RX payload bytes per GPD (64–16384) |
| `ruby_txslot` | 2 | TX FIFO slot count (0–7); 3 units per endpoint at 2 |
| `ruby_rxslot` | 2 | RX FIFO slot count (0–7) |
| `ruby_txfbase` | 0 | TX FIFO base byte override |

### Endpoint selection (0334 line)

| Argument | Default | Purpose |
|---|---|---|
| `ruby_txep` | 1 | TX endpoint index; only 1 and 3 are accepted |
| `ruby_rxep` | 1 | RX endpoint slot 1–16 (evidence builds use 2) |
| `ruby_fifo_plan` | 0 | read-only FIFO budget probe: print fit/REJECT for N units |
| `rubyep_test` | 0 | 0331 test channel (`t331 …`), including 0334 `epmap/epall` |

### QMU / interrupts

| Argument | Default | Purpose |
|---|---|---|
| `ruby_qstart_cfg` | 0 | start the empty TX ring at configure time |
| `ruby_qstart_keep` | 0 | keep the queue started across reconfigures |
| `ruby_qisar0_isr` | 0 | clear the TX-done bit from the ISR |
| `ruby_qisar1_w` | 1 | write QISAR1 aggregate bits |
| `ruby_qstart_ms` | 0 | delayed Q_START time |
| `ruby_qstart_only` | 0 | Q_START without the rest of the sequence |
| `ruby_lpmhrwe`, `ruby_lpmmask`, `ruby_lpm_fc` | 1/1/0 | LPM and flow-control parity bits |
| `ruby_usbintr`, `ruby_usb2parity` | 1/1 | vendor USB2 interrupt/parity init |

### TX recovery and tracing

| Argument | Default | Purpose |
|---|---|---|
| `ruby_txbell`, `ruby_txbell_ms` | 0 / 1 | TX doorbell poll ring |
| `ruby_txreset`, `ruby_txeprst`, `ruby_tx_eprst_bit` | 0 / 0 / 0 | TX reset strategy and EP_RST bit override |
| `ruby_txreplay` | 0 | replay un-fetched GPD payloads after a rebuild |
| `ruby_recover` | 0 | recovery mask bits 0–2 |
| `ruby_clrhalt`, `ruby_clr81`, `ruby_devrst_pre`, `ruby_cfgrst` | 0 | clear-halt/device-reset variants (0–2 for cfgrst) |
| `ruby_txfifo`, `ruby_txdone`, `ruby_noise`, `ruby_txdeq`, `ruby_txpio`, `ruby_txpiotail`, `ruby_dmareq_pio`, `ruby_qisar0_isr` | 0 (txdone/txfifo 1) | per-packet traces and PIO variants |
| `rubyusb_hotplug`, `rubyusb_susp`, `rubyusb_window_ms` | 0 / 0 / 30000 | 0333 port events, suspend gate, enumeration window |

## Image packaging parameters

| Stage | Tool | Parameter | Current value |
|---|---|---|---|
| Payload | `.temp/mkpayload.py` | `kernel` | `kernel.development.sweet` |
| | | `adt` | project `adt-identity.bin` (not in this repository) |
| | | `out` | `payload-*.bin` |
| | | `--cmdline` | one of the three presets above (587/605/585 B) |
| | | `--ramdisk` | unused for the normal path (`rd=md0` rescue only) |
| Boot image | `tools/image/pack_boot.py` | `--base` | stock/Magisk 128 MiB image (external) |
| | | `--shim` | raw loader shim (external) |
| | | `--payload` | output of `mkpayload.py` |
| | | `--out` | `x16-*.img` |
| | | `--seed` | `0x84` (deterministic filler) |
| | | `--payload-off` | optional offset override |
| | | `--expect-base-sha` / `--expect-shim-sha` / `--expect-payload-sha` / `--expect-out-sha` | optional reproducibility gates |
| Verify | `tools/image/boot_verify.py` | image | layout + cmdline dump |

Reproducibility rule: pack the same base/shim/payload with the same seed and
compare `--expect-out-sha`; the 0084 image cannot be byte-reproduced because it
used random filler (compare with `boot_layout.py` instead).

## See also

- [14 — USB per-endpoint queues](14-usb-per-endpoint.md)
- [11 — CI baseline and branch pins](11-ci-baseline.md)
- [12 — USB host channel](12-usb-host.md)
