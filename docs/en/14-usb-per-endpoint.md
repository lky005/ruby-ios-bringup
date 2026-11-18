# 14 — USB per-endpoint queues and FIFO allocation (0333–0334)

**English** · [中文](../zh/14-usb-per-endpoint.md)

> Status tags follow the [repository README](../../README.md). A number
> without a source is a bug; commands use placeholders, never personal paths.
> This chapter covers the device-mode queue work; the host-side channel
> remains [12](12-usb-host.md) and the 0180–0195 EP2 history remains
> [13](13-usb-ep2-golden.md).

## Scope

The 0333/0334 line builds on the 0195 EP2 state machine:

- **0333** — controller events (LINK speed change, MAC2 suspend/resume), a
  unified port state machine with reattach on the workloop, and a gated U2
  suspend freeze. `rubyusb_hotplug=1` and `rubyusb_susp=1`; both default 0.
- **0334** — every endpoint slot gets its own GPD ring, the per-endpoint
  CSR/QMU/HIAR offsets follow the vendor strides, and the FIFO budget probe
  became an actual allocation. Tested through the 0331 channel with the new
  `t331 epmap / eptx / eprx / epall` commands.

## What is verified (2026-11-18) [measured]

Build and pins:

| Item | Value |
|---|---|
| Patchset | `d87e666f…` (305 files) |
| CI | `xnu-0334` run `44296779724` (success) |
| CI kernel | full `5ee3019d…`, exec-data `61c6b1a1…` (`config/0334.env`) |
| Device images | default `561f1026…` (587 B cmdline), lite `b4b95789…` (585 B, `rubyep_test=1`) |

Device runs (lite image, then default image):

1. 0331 lite matrix **PASS** — T0/T1/T3/T4; 512/1024/4096/16384 B all
   `DATA-OK` + `CRC-OK`.
2. `t331 epmap` — TX and RX both allocate
   `0x0 / 0x600 / 0xc00 / 0x1200 / 0x1800` for EP1–5 and refuse EP6–8:
   ```
   RUBY CFG: 0334b4 epfifo tx ep1 addr=0x0 units=3
   ...
   RUBY CFG: 0334b4 epfifo tx ep6 REJECT units=3 free=1
   ...
   RUBY CFG: 0334b4 epfifo tx_free=1 rx_free=1 ep0_cap=512
   ```
3. `t331 epall 511` — mailbox
   `ok_tx=3e tmo_tx=00 err_tx=1c0 ok_rx=3e err_rx=1c0 restore=0`; the device
   printed `st=0` for EP1–5 on both directions:
   ```
   RUBY EP TEST: 0334b4 epall tx ep=1 addr=0x0 st=0
   ... tx ep=5 addr=0x1800 st=0
   RUBY EP TEST: 0334b4 epall rx ep=1 addr=0x0 st=0
   ... rx ep=5 addr=0x1800 st=0
   RUBY EP TEST: 0334b4 epall done ok_tx=3e tmo_tx=00 err_tx=1c0
   ok_rx=3e err_rx=1c0 restore=0
   ```
4. RX rings are independent per slot and the default is restored:
   ```
   RUBY USB: 0334b3 rx ring sel=1 pa=0x1420f0000 uc
   RUBY USB: 0334b3 rx ring sel=2 pa=0x1420f4200 cached
   RUBY USB: 0334b3 rx ring sel=3 pa=0x1420f4300 cached
   RUBY USB: 0334b3 rx ring sel=4 pa=0x1420f4400 cached
   RUBY USB: 0334b3 rx ring sel=5 pa=0x1420f4500 cached
   RUBY USB: 0334b3 rx ring sel=1 pa=0x1420f0000 uc   (restore)
   ```
5. The lite matrix **PASS** again after the batch — the EP1 restore keeps the
   default data path alive.
6. Default image: `0334b3 rx ring sel=1 uc`, **no** `0334b4 epfifo` lines at
   boot, WinUSB `CM_PROB_NONE`, no panic, `fused=0`.

## Patch range

`bsd/dev/ruby_usb.c` is created by `0086-ruby-usb-p0.patch` and evolves
through the numbered USB patches. `0329a`–`0329a6` split it into
`ruby_usb_ep`, `ruby_usb_qmu`, `ruby_usb_plat`, `ruby_usb_port` and
`ruby_usb_gadget`; `0330` adds the configuration layer, `0331` the EP0 test
channel, `0332*` the gated BOS/MS OS descriptors, `0333` the port events and
`0334` the per-endpoint queues. The patches apply in order and nothing is
dropped, so `ci/prepare-baseline.sh` reconstructs the complete
`bsd/dev/ruby_usb*.c/h` set from the 0086–0334 patch list alone. (`0080` is
the UFS patch and does not touch USB.)

## Design

### Per-slot rings

- TX: slot 1 keeps the verified BSS/UC 1 KB ring; every other slot uses its
  own cached 1 KB ring (`ruby_gpd_ring_slots[16]`).
- RX: slot 1 keeps the page-aligned BSS/UC ring; every other slot uses its own
  cached 256 B ring. Payload buffers stay shared, so only one ring per
  direction carries traffic at a time.

### Per-endpoint registers

Offsets follow the vendor strides (mtu3 `MU3D_EP_TXCR/RXCR`, `USB_QMU_TQ/RQ`):

| Register | Formula |
|---|---|
| TX CSR0/1/2 | `0x0110 + (ep-1)*0x10` (+0/+4/+8) |
| TX TQ CSR/SAR/CPR | `0x0510 + (ep-1)*0x10` (+0/+4/+8) |
| TX HIAR | `0x0484 + (ep-1)*4` |
| RX CSR0/1/2 | `0x0210 + (ep-1)*0x10` (+0/+4/+8) |
| RX RQ CSR/SAR/CPR | `0x0610 + (ep-1)*0x10` (+0/+4/+8) |
| RX HIAR | `0x04c4 + (ep-1)*4` |
| TX-done bit | `BIT(0) << ep` |

### FIFO allocation

`ruby_epfifo_map()` mirrors vendor `ep_fifo_alloc()`:

- 512 B units; `units = roundup_pow_of_two(ceil(mps / 512)) * (slot + 1)`.
- This IP runs slot 2 (the TWRP dump shows EP2 at byte 1536), so each endpoint
  takes 3 units and one direction fits `16 / 3 = 5` endpoints.
- `CSR2 = FIFOADDR(addr >> 4) | FIFOSEGSIZE(ilog2(512))`; EP0 has its own
  `CAP_EP0FFSZ` block, so the per-direction pool starts at address 0.
- EP6–8 are refused with a bounded print instead of overlapping segments.

### Completion in IRQ mode

With `rubyqmuirq=1` the 1 ms QMU path can consume and clear the QISAR0 done
bit before the poll reads it, so a moved `TQCPR` is the primary completion
evidence and the done bit is the fallback.

## Negative result kept for the record

The first 0334b4 build used `fifo_addr == 0` as the "unallocated" sentinel.
EP1's segment address is legitimately 0, so EP1 failed:
`ok_tx=3c err_tx=1c2 ok_rx=3c err_rx=1c2` with `st=22`. Fixed with an explicit
`0xffffffff` sentinel; the runs above are the fixed build.

## Reproduce

```sh
# lite image must carry rubyep_test=1 (see the boot-args appendix)
python tools/host/ruby_usb_ep_test.py --matrix lite
python tools/host/ruby_usb_ep_test.py --cmd "t331 epmap"
python tools/host/ruby_usb_ep_test.py --cmd "t331 epall 511"
python tools/host/ruby_usb_ep_test.py --matrix lite   # restore check
```

Expected: matrix PASS, allocations `0x0/0x600/0xc00/0x1200/0x1800`, EP6–8
`REJECT`, `ok_tx/ok_rx = 0x3e`, `err = 0x1c0`, `restore = 0`.

## Limits (not guaranteed)

- The host tool is fixed on endpoint `0x81`, so EP2–8 have QMU-side evidence
  only; there is no host-visible data check on them.
- RX slots prove arm + `RQCSR` START; the host does not write the
  non-default OUT endpoints.
- Five endpoints per direction is a capacity result; concurrent multi-EP
  interference was not measured.
- A slot-1 variant that would fit 8+8 endpoints was not tested.
- Selective suspend and hotplug were not re-tested in this round; 0333
  evidence stands at 10/10 re-enumeration and two suspend cycles.

## See also

- [12 — USB host channel](12-usb-host.md)
- [13 — EP2 state machine (0180–0195, historical)](13-usb-ep2-golden.md)
- [Appendix — boot arguments and packaging](appendix-bootargs.md)
