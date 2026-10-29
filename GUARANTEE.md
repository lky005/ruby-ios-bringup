# Reproducibility guarantee

**English** · [中文](GUARANTEE.zh.md)

**Status 2026-10-22 — documented recipe with one-unit device evidence.**
B+NOP first boot -> A', a CI kernel boot, and a real-touch 0085 boot were
observed on the author's unit. This is not an independently reproduced
second-unit or clean-room guarantee. Detailed test guarantees are deferred.

**Scope note (2026-10-29):** this guarantee covers the historical 0085/0084
success bundle only. The 2026-10-29 main line uses the pins in
`config/0140.env` and `config/0131b.env`; see `docs/en/11-ci-baseline.md`.

## Scope

Only the success path is covered:

```
stock LK -> XNU 8796 -> iOS 16.7.16 userland
  -> lock screen -> real bottom-edge swipe (0085) -> SpringBoard home screen
  or -> synthetic swipe (0084) -> SpringBoard home screen
```

Failed routes are historical evidence, not covered by this guarantee.

## Definition

Given all of the following:

- the same device situation (ruby / MT6877, Android 12 / MIUI 13.0.4, unlocked,
  slot `_a`, the partition layout in `docs/en/device.md`);
- the same boot image and iOS root/ICL state (hashes below);
- the boot args in `config/0085-boot.cmdline` (or `config/0084-boot.cmdline`
  for the synthetic-swipe image);
- the documented procedure in `docs/en/09-reproduce.md` and
  `docs/en/05-userland.md`;

the success state is **expected** to reproduce. One author's unit was tested on
2026-10-22; no second-unit or clean-room device validation has been performed.

If any hash differs, this guarantee does not apply; treat it as a different
configuration.

## Success bundle

| Item | Value | Note |
|---|---|---|
| Baseline | `MakrSas/ios-topaz@5095ac1` | upstream commit |
| Patchset (0085) | `cf4008e3...` | 88 files; recipe output; same as the harness build |
| Patchset (0084) | `de1824c2...` | 87 files; previous milestone |
| 0010/0012 change | `1edb6633...` | small baseline patch |
| Real-touch kernel | `9eb9acac...` | 0085; exec-data `e4823afb...` |
| Real-touch image | `ace60d16...` | external; not in the repo |
| Reference kernel (0084) | `b38fca5f...` | the previous kernel that booted |
| CI rebuild (0084) | `8a80855d...` | run `39648068844`; booted; payload tool ref `33852e3` |
| Boot image (0084) | `94c639d1...` | external; not in the repo |
| Root image (A) | `e698339d...` | external; success snapshot; verify before use |
| ICL original block | `ae317804...` | restore path |
| ICL patched block | `4a489542...` | bypass |
| Boot args | `config/0085-boot.cmdline` | real-touch cmdline; `0084` is the previous milestone |
| Success criterion | all timings from the Apple logo: first boot ~60 s (58 s measured); warm reboot ~22 s; 2026-10-22 B+NOP first boot 22 s / 30 s; swipe to home; animations | author's boot22/boot23 and 2026-10-22 run |

Root states (all external; full images are not in the repo):

| State | SHA-256 | Meaning |
|---|---|---|
| A success | `e698339d...` | post-boot22; ICL NOP + first-boot state |
| B pre-boot22 | `985c30...` | pulled+seeded; ICL original; the boot22 diff maps B -> A |
| C clean base | `34c2882d...` | mkiosroot + tweaks; first boot/seed needed |
| A' first boot | `55e2ab2c...` | one B+NOP first-boot snapshot; new first boots differ |

The success bundle is A. The previous pin named B; it was corrected on
2026-10-22 after a read-only root audit. A' is a first-boot snapshot, not a
stable pin; post-boot hashes are volatile.

Full hashes:

```text
patch85    cf4008e309cfa566e3df968592a2d3f3224a9b3d0813d6054326115fecc0a03f
kernel85   9eb9acac8a4c936c1861fba1e0d29c105b714e8d0e6d407b48f4237076e6b947
execdata85 e4823afb97360e24708184d09c0dc6c9f7280e33d5c4aefbeb901b3fa9b11e3e
image85    ace60d1645ec271cdbd55b7007456cb578168ca708382aafae8fbf506e68f6c8
payload85  dbc57e96396f2e3e23213a76d300b1a329e2b4a320bc7363cf99ce0fc9e52b1c
ci85 kern  904e10dfc14c5e9cc0abd8a6ad7a8b6399526e31a33deb64ceb93cdde0a30d12
ci85 image 54d1b3066a3782cab36135dbe8d666cf53bbd6837b8394105d7e61de9b32b10d
patch84    de1824c28b5e56f7c60988c33501cd5bbfd24a4159d9358223fd2af11392d360
0010/0012  1edb66332bb4daa8b1abcd6c4de77a0e88ed9c7e9bb4a2a7045a2696e53ab338
kernel84   b38fca5f38cfb721e21228eac4dd4b355000d1b850bdf204afba9ff8b8d1afcd
ci kernel  3ceb9b3490f8c8ecaa74348c3c5cb02d7302d0ec7f87006fe8354e9d2011a831
ci kernel2 8a80855d1f615cf72f6ebb9f6213d0d55c8f799ad80286f0aab9f80d3215f38a
ci payload 2749bf1cf398f750d25ed6e84bbb529d5cc5ba3e1ef6be464bff09d0ec87a053
ci image   87dd4910247cf746df281e77cdf8d63528a148757a82e2b97be58ee5d9183162
boot84     94c639d1f45197718c62bd09c32c72b39710ba23de60f4a04bba96014bce1cb6
root A     e698339d0e228609c2d98f16ae8dd44a5149f2ccc19a44b98d5d08845c53f96f
root B     985c30fcca28cb79e6ad6d30a1ff4b4b6b7306b69d6e480cd7cccf4fb5ca11e3
root C     34c2882d3b722e53c9755dad3b74284d6ebba6f00256838d407ba3694b1a456d
root A'    55e2ab2c6e5494f473ece06a1c2bed728ed528bb257b67f01413d1aa51c76f11
icl orig   ae3178046fe7cb9e08291c39dc4773429be26c35472c6fbd9135d5f2a225fd73
icl pat    4a4895422dcec766b90b65c067ecb06ef8fd3e346c03ee7e2464a85f62a73b74
```

The root and boot images are **not** included: they contain Apple/Android
material that cannot be redistributed. The hashes are the contract.

Device-baseline hashes (GPT/boot/vbmeta) are intentionally **not** published;
they can fingerprint the unit. The device situation is described in
`docs/en/device.md`; only the artifact hashes above are the contract.

## Hash stability

Fixed / pre-boot (identity): the 0085 patchset `cf4008e3...` and 0084 patchset
`de1824c2...`, boot args, ICL blocks, the named root snapshots (A/B/C/A') and
the named kernel/payload/image artifacts for a specific run. Kernel CI builds
are not bit-identical; the patchset hash is the source gate and the Mach-O
exec-data hash is the artifact-level gate; record the actual full artifact hash
for each run. The 0085 exec-data reference is `e4823afb...`. A' is one first-boot
snapshot; a new first boot is a new state.

Volatile / post-boot (do not require these to match): the live root after any
boot (A' -> A''), UUIDs/timestamps, logs and caches, the SWEETLOG ring and its
decoded text, and UI pixels/timing. The contract is pre-boot identity plus
behavior (lock screen, autoswipe, desktop, ring markers), not a post-boot
whole-disk hash.

## Guaranteed

- The patchset and recipe: the workflow refuses to build unless the recipe
  reproduces `cf4008e3...` (88 files). The first 0085 CI run `39694456200`
  succeeded; its exec-data hash matched the booted kernel.
- The offline tools: host checks, synthetic and real ICL block round-trips.
- The documented success-path procedure and its scope.
- The 2026-10-22 one-unit device evidence (B+NOP first boot -> A', CI kernel
  boot), as recorded evidence; it is not a second-unit guarantee.
- Historical evidence for failed routes, clearly marked as not supported.

## Rebuild

`scripts/build-payload.sh` + `tools/image/pack_boot.py` with the inputs above
and seed `0x84` produce `a0ce0fe1...`. The rebuild is layout-equivalent to the
original image, **not** byte-identical: the original used `os.urandom` filler.
Use `tools/image/boot_layout.py` to compare a rebuild; the success image
remains `94c639d1...`.

## Not guaranteed

- An independent device boot on another unit.
- Exact UI pixels, timing or app state.
- A different CI build or payload, or a second-unit boot of the CI-rebuilt
  kernel. The 2026-10-22 run booted on the author's unit with payload ref
  `33852e3`; the strict pinned rebuild is open.
- Post-boot live-root/ring/log hashes, A' across first boots, and UI timing.
- The external root builder and shim/ADT builder as clean-room tools.
- Regression of the original (unpatched) ICL block.
- The root/boot artifacts themselves (not included).
- A byte-identical rebuild of the original boot image (its filler was random).
- Any failed route's device behavior.

## Deferred validation

Deferred due to time and effort, not because they are known to fail:

- second-unit boot test;
- Linux clean-room host CI;
- strict pinned payload rebuild (the 2026-10-22 test used ref `33852e3`);
- root builder and shim/ADT builder as clean-room tools;
- original ICL block regression;
- keys and USB;
- long-run stability;
- second-unit/clean-room device regression; the one-unit first boot and CI
  kernel were run on 2026-10-22.

Device-baseline hashes (GPT, boot_a/b, vbmeta) are intentionally not
published; the device is described in `docs/en/device.md` instead.

These are explicit open items. The document records one-unit device evidence
and the documented recipe; it is not yet a second-unit guarantee.

## How to use

1. Compare your device situation and artifact hashes with the table above.
2. Follow `docs/en/09-reproduce.md` and `docs/en/05-userland.md`.
3. If a hash differs, stop: it is a different configuration, not a covered
   reproduction.
4. If you perform an independent run, record the hashes and result (sanitized)
   and update this document.

## Failed routes

`patches/historical/0081-0083` and the failure catalogue in
`docs/en/07-experiments.md` are kept as evidence. They are **not** part of the
success build, are not re-tested on a device, and are not guaranteed.
