# 13 — USB EP2: state machine, golden PHY, and limits (0180–0195)

**English** · [中文](../zh/13-usb-ep2-golden.md)

Evidence tags: **[measured]**, **[inferred]**, **[historical]**. A number
without a source is a bug; commands use placeholders, never personal paths.

## Scope

This chapter covers the device-mode USB EP2 bulk-IN log channel of the ruby
(MT6877) port: the 0180–0189 QMU/ring state-machine line, the 0194 golden PHY
value, and the host-side behaviour measured with the probe channel. The 0195
patch is a comment-only bilingual acknowledgement in the driver header.

| Item | Value |
|---|---|
| Line | 0195 |
| Patchset | 0194 `70597a6c…` (186 files); 0195 `a9cc0050…` (187 files) |
| Kernel | 0195 full `45ea1bc3…`, exec `6b22fc25…` (verified unchanged); 0194 full `6d51fa71…` |
| Image | 0195 `fe009b89…` (`x16-0195-ack.img`, built not flashed); 0194 `1808e440…` (`x16-0194-golden-srctrl.img`) |
| Boot gate | `RUBY USB: golden acr5=0x40805000`; 14.1 s to enumeration |
| Open | XactErr root cause; 512 B aggregation; host-port stability |

## 1. What the EP2 line fixed

The log channel is a QMU bulk-IN ring: the kernel writes a 16 B header plus up
to 495 B of text into a log slot, a 16 B GPD describes it, and the QMU sends
one packet per slot. The host reads EP2 IN; a bad transaction surfaces as an
EPIPE/XactErr.

| Patch | Single variable | Frames before EPIPE | Reading |
|---|---|---:|---|
| 0180 | QCR1 TX ZLP | 41 / 40 | not the cause; XactErr remains |
| 0181 | GPD clean publish order | 23 | cache order is not sufficient |
| 0182 | GPD dump hook | 14 | hook did not fire on the host path |
| 0183 | dump before `EP_RST` | 3 | GPD 20–32 are legal; no fixed window |
| 0184 | cap in-flight at 16 | 37 | >16 failed; **ring-full falsified** |
| 0185 | RX eye 6/3/2/13 + noise | 33 | **RX eye excluded** |
| 0186 | HS TX slew calibration | 1 | `fm_out=0`; fallback used |
| 0187 | vendor init order + board eye | 21 | order is not the FM cause |
| 0188 | state reset on `EP_RST` | 10 | QMU left inactive |
| 0189 | stop → ring reset → start | 31 / 22 | `gap=0 inv=0`, QMU active |

[measured] 0189 is the state-machine fix: the QMU is stopped before the ring
reset, the FIFO is flushed (double `TX_FLUSHFIFO` around the ACTIVE poll), and
the queue is started again. The software ring and QMU stay in sync; a physical
replug re-runs `CFG_IN / TXCFG_IN / EPRST_TX` and the state reset, and the
first read is non-zero.

The remaining failure is host-visible: `USBD_STATUS_XACT_ERROR`
(`0xC0000011`) after a random number of frames. The device-side counts stay
clean (`TQERRIR0=0`, `gap=0`, `inv=0`, no `TX_SENTSTALL`).

## 2. Golden PHY (0194)

The board eye values are `vrt=6, term=3, rev6=2, disc=13` (the field earlier
described as "pre-emphasis" is PHY REV6). They follow the upstream device-tree
bindings and the board `ruby-mt6877.dtsi` values. The SRCTRL sweep on the live
board:

| SRCTRL | ACR5 | Reads (frames) | Note |
|---:|---|---|---|
| 1 | `0x40801000` | 33, 4; 31, 22 | baseline; large variance |
| 4 | `0x40804000` | 3, 4; 1 (0186) | poor |
| **5** | **`0x40805000`** | **21, 44; 62 peak** | best observed |
| 6 | `0x40806000` | 19, 13 | clean, below 5 |
| 7 | `0x40807000` | 3, 7, 8 | poor; short frames |

[measured] The FM slew calibration never oscillated on this port (`fm_out=0`
in every order/cold test). 0194 retires it and writes `ACR5=0x40805000`
directly; the boot log shows:

```
RUBY USB: PHY eye acr1=0x00846300 acr6=0x801004d2
RUBY USB: golden acr5=0x40805000
RUBY USB: IPPC ready (s1=0x00013d0f s2=0x00000001)
RUBY USB: EP2 state reset enq=0 deq=0 inflight=0 fifo_empty=1
```

The 62-frame peak is a single clean-session sample; the spread is large
(4–62). SRCTRL=5 is the best observed value, not a guarantee.

## 3. Host-side behaviour

**Frame length is variable.** A frame is `16 B header + up to 495 B text`;
511 B is the maximum, not a fixed size. When the log text is shorter, the
frame is shorter. The earlier "short packet = FIFO residue" hypothesis was
falsified: after a full `CLEAR_FEATURE` with `fifo_empty=1`, a 20 B frame
continued the previous log line, and 91 B frames were `EP2 no_log`
diagnostics with `total == pos`. Short frames are legitimate log slices.

**Big reads do not aggregate.** A 4 KB or 16 KB read still returns one 511 B
short packet. The 511 B packet is short relative to the 512 B maxpacket, and a
short packet ends the URB. Aggregation would require 512 B frames, a new
framing change.

**Pacing is not the cause.** 2 ms, 5 ms and 10 ms reads all fail after a
random number of URBs (2–50). 2 ms produced the longest run (50); 10 ms did
not consistently last longer. The failure is per-URB, not bus heat or a fixed
handshake timeout.

**Transparent resume is endpoint-level only.** A standard
`CLEAR_FEATURE(0x82)` recovers the endpoint and the stream continues; a run of
50–320 clears eventually makes the host port drop. The XNU kernel survives
(the PHY registers persist, no boot banner), but a physical re-enumeration is
required. Application-level clear cannot recover the host port.

**ETW stops at the generic error.** The captured UCX completion is
`USBD_STATUS_XACT_ERROR (0xC0000011)`; there is no CRC, toggle-mismatch,
STALL, overrun or babble status. xHCI completion code 4 is a generic
"transaction error" after retries. Sub-classification needs a USB2 protocol
analyser; ETW cannot provide it.

## 4. Reproduction

The kernel CI is content-pinned; the image build uses an external base, shim
and ADT that are not in this repository. Full-file kernel hashes are artifact
pins; the exec hash is the reproducibility gate — full-file hashes can differ
between checkouts because of DWARF/path metadata.

```sh
# kernel: the 0195 ack is comment-only; the 0194 exec pin is the reference
gh workflow run xnu.yml --ref <branch> \
  -f hash_config=config/0195.env \
  -f patchset_sha256=a9cc0050432d4259f38c2e5431e0ac05eecf95c3a78324ad94f11283d8031983

# image (base/shim/ADT are supplied by the user)
python tools/image/pack_boot.py --base <base> --shim <shim> \
  --payload <payload> --out <image>

# flash and boot gate (placeholder slot; keep a recovery image)
fastboot flash <slot> <image>
```

Pass: `RUBY USB: golden acr5=0x40805000`, `PHY eye acr1=0x00846300
acr6=0x801004d2`, and enumeration. Rollback: flash the previous verified image
to the active slot; keep a recovery image.

## 5. Limits

- XactErr (`0xC0000011`) is not root-caused; ETW cannot sub-classify it.
- 511 B short-packet framing prevents big-read aggregation.
- A sustained clear storm can drop the host port; the kernel survives but a
  re-enumeration is required.
- 62 frames is a peak sample, not a guarantee; the 0180–0195 line is research
  bring-up, not a stable USB function driver.

## Acknowledgements / 致谢

**English.** The MTU3/QMU and U2 PHY work in this chapter was developed
against public documentation (including upstream device tree bindings) and
cross-checked with the MediaTek vendor `mtu3`/`phy-mtk-tphy` drivers
(Linux 4.19, GPL-2.0) and the upstream Linux `mtu3` driver (GPL-2.0),
especially commit [`5aba179c34`](https://github.com/torvalds/linux/commit/5aba179c34)
("usb: mtu3: fix the failure of qmu stop") by Chunfeng Yun (MediaTek),
reported by Min Guo. The HS TX eye fields (vrt/term/rev6/disc; the field
earlier described as "pre-emphasis" is PHY REV6) follow the upstream
device-tree bindings and the board `ruby-mt6877.dtsi` values; the QMU stop
path uses the double `TX_FLUSHFIFO` sequence from that commit. Those trees
are references only and are not included in this repository; the driver is
original XNU glue and remains under APSL 2.0 as part of the XNU patches.

**中文。** 本章的 MTU3/QMU 与 U2 PHY 工作依据公开文档（包括上游设备树 YAML
绑定）开发，并与 MediaTek 厂商 mtu3/phy-mtk-tphy 驱动（Linux 4.19，
GPL-2.0）及上游 Linux mtu3 驱动（GPL-2.0）交叉核对，特别是 Chunfeng Yun
（MediaTek）的 [`5aba179c34`](https://github.com/torvalds/linux/commit/5aba179c34)
（"usb: mtu3: fix the failure of qmu stop"，Min Guo 报告）。HS TX 眼图字段
（vrt/term/rev6/disc；此前称为 "pre-emphasis" 的字段实为 PHY REV6）遵循
上游设备树绑定和板级 `ruby-mt6877.dtsi` 取值；QMU stop 路径采用该 commit
的双 `TX_FLUSHFIFO` 序列。上述源码仅作参考，未包含在本仓库中；驱动为原创
XNU 胶水实现，作为 XNU 补丁的一部分仍按 APSL 2.0 发布。

## Evidence map

- Public records: [STATUS](../records/STATUS.md),
  [VERIFICATION](../records/VERIFICATION.md),
  [ACKNOWLEDGEMENTS](../records/ACKNOWLEDGEMENTS.md).
- CI: `42295463255` (0194), `42301546006` (0195 xnu), `42302515812`
  (0195 host-checks), rerun `42302694315` (exec pin proof, success).
- This chapter is a public summary; it does not link private run cards.
