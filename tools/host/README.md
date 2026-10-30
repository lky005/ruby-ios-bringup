# Host USB tool (reference)

`ruby_usb_host.py` is the stable host-side session manager used for the
0143 USB bring-up runs. It talks to the kernel USB log channel over EP2
(vendor request set) and to the EP0 diagnostics over control transfers.

It is **read-only over EP0**. The only device writes are:

- one text line to EP2 OUT (`cmd`), and
- the optional `--pcycle` one-shot `pnputil /restart-device` attempt.

There is no 0x2D MMIO write path in this copy.

## Requirements

- Python 3.10+.
- `pip install pyusb libusb-package`.
- Windows: a WinUSB driver bound to the vendor-specific device
  `1209:0002`. If Windows binds a serial/CDC driver instead, the tool
  cannot open it; rebind with WinUSB (Zadig or an equivalent tool) and
  verify with `status`.
- Linux/macOS: libusb must be able to claim the interface; `--pcycle` is
  Windows-only.

## Usage

```sh
python ruby_usb_host.py status
python ruby_usb_host.py cmd "help" --drain-secs 3
python ruby_usb_host.py cmd "help" --drain-secs 3 --pace-ms 0   # burst repro
python ruby_usb_host.py watch --pace-ms 5 --log session.log
```

- `status`: one-shot EP0 snapshot: 0x27 EP0 counters, 0x23 RX
  diagnostics, 0x2B log length, and `EP_RST`/`TX2CSR0`/`TQCSR2`/
  `TQCPR2`.
- `cmd`: writes `<line>\n` to EP2 OUT and drains EP2 IN for
  `--drain-secs` at `--pace-ms` (default 5 ms; 0 = burst).
- `watch`: paced long session; on EPIPE the IN reader stops but EP0
  stays usable; it reconnects with backoff when the device re-appears.
- `--pcycle`: at most one restart attempt when the device is still
  enumerated but wedged. It needs an elevated shell and may fail or
  drop the device; do not loop it.

## Output notes

- EP2 replies are 511-byte frames (16-byte header + text) for the 0143
  kernel; read size is 512.
- `0x22` packs `inflight`, `enq` and `deq` as 4-bit fields. The tool
  prints them as `*_nibble` and derives `outstanding = push_seq -
  txdone`; do not read a nibble as a full count.
- On EPIPE/XACT the tool logs `[ep2-in] ...` and runs a one-shot
  `abort_snapshot` (0x21/0x22/0x23 + key registers) while EP0 is still
  alive.
- `frames=... unique=... holes=... dup=...` summarises the last
  session.

## Safety

- Run one host tool at a time; the OUT command channel has one writer.
- EP0 requests use a 3 s timeout; EP2 reads poll at 200 ms. Do not lower
  the EP0 timeout or hammer retries.
- A single `clear_halt(0x02)` after `claim_interface(0)` can recover a
  halted OUT pipe; never put clear_halt in a loop and do not clear EP2
  IN repeatedly.
- Do not run `pnputil /restart-device` in a loop; once the device is
  gone (`NO_DEVICE`) a physical reboot is the reliable recovery.
- Do not scan MTU3 FIFO/data registers or write MMIO through this tool.
  The 0x2C probe is whitelist-only; see the main document.

See `docs/en/12-usb-host.md` (Chinese: `docs/zh/12-usb-host.md`) for
test conditions, protocol details and the full do/don't list.
