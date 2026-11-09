#!/bin/sh
# Build the pinned baseline patchset without vendoring the upstream tree.
#
# Baseline source (one of):
#   BASELINE_DIR=DIR       content-pinned 82-file sweet 0001-0079 set
#                          (private mirror or a local bundle). The manifest
#                          root is verified before anything is applied.
#   ALLOW_PUBLIC_UPSTREAM=1
#                          fetch MakrSas/ios-topaz at BASE_SHA and remove the
#                          topaz-specific patches by name (external fallback,
#                          same manifest verification).
#
# Then: add this project's patches, apply the small 0010/0012 change, normalize
# to LF and verify the canonical patchset hash.
#
# Usage: [BASELINE_DIR=dir] sh ci/prepare-baseline.sh [DEST]
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BASELINE_DIR=${BASELINE_DIR:-}
BASELINE_MANIFEST_SHA256=${BASELINE_MANIFEST_SHA256:-829d759826607027bc4a1d9818b6dd4956a312a087217b6ce7e5ce31fa3ae910}
BASELINE_FILES=${BASELINE_FILES:-82}
ALLOW_PUBLIC_UPSTREAM=${ALLOW_PUBLIC_UPSTREAM:-0}
BASE_REPO=${BASE_REPO:-https://github.com/MakrSas/ios-topaz.git}
BASE_SHA=${BASE_SHA:-5095ac19dbdcf37b64b81fe443f4027ad51b84bf}
PATCHSET_SHA256=${PATCHSET_SHA256:-8c7b4ea1dfd41a60a2c82000d9bd19e136d33f53e0dab0e0f68e9273136d6aed}
SKIP_PATCHES=${SKIP_PATCHES:-}
PYTHON=${PYTHON:-python3}
DEST=${1:-baseline}

if [ -e "$DEST" ]; then
    echo "prepare-baseline: $DEST already exists" >&2
    exit 2
fi

if [ -n "$BASELINE_DIR" ]; then
    BASELINE_SRC="$BASELINE_DIR/xnu/patches"
    if [ ! -d "$BASELINE_SRC" ]; then
        echo "prepare-baseline: missing $BASELINE_SRC" >&2
        exit 4
    fi
    mkdir -p "$DEST/xnu/patches"
    git init -q "$DEST"
    cp "$BASELINE_SRC"/*.patch "$BASELINE_SRC"/*.sh "$DEST/xnu/patches/"
elif [ "$ALLOW_PUBLIC_UPSTREAM" = "1" ]; then
    git init -q "$DEST"
    git -C "$DEST" remote add origin "$BASE_REPO"
    git -C "$DEST" fetch -q --depth 1 origin "$BASE_SHA"
    git -C "$DEST" checkout -q FETCH_HEAD
    actual="$(git -C "$DEST" rev-parse HEAD)"
    if [ "$actual" != "$BASE_SHA" ]; then
        echo "prepare-baseline: baseline mismatch: $actual" >&2
        exit 3
    fi
    # Normalize before removing the topaz-specific patches by name.
    "$PYTHON" "$ROOT/ci/normalize_lf.py" "$DEST/xnu/patches"
    while IFS= read -r name; do
        [ -n "$name" ] || continue
        if [ ! -f "$DEST/xnu/patches/$name" ]; then
            echo "prepare-baseline: missing topaz patch: $name" >&2
            exit 4
        fi
        rm -f "$DEST/xnu/patches/$name"
    done < "$ROOT/ci/topaz-patches-to-remove.txt"
else
    echo "prepare-baseline: set BASELINE_DIR (private baseline) or ALLOW_PUBLIC_UPSTREAM=1" >&2
    exit 4
fi

# Normalize and verify the 82-file baseline before this project's patches.
"$PYTHON" "$ROOT/ci/normalize_lf.py" "$DEST/xnu/patches"
if [ -n "$BASELINE_DIR" ] && [ -f "$BASELINE_DIR/MANIFEST.sha256" ]; then
    "$PYTHON" "$ROOT/ci/baseline_manifest.py" --patches "$DEST/xnu/patches" \
        --expect-root "$BASELINE_MANIFEST_SHA256" --expect-count "$BASELINE_FILES" \
        --manifest "$BASELINE_DIR/MANIFEST.sha256"
else
    "$PYTHON" "$ROOT/ci/baseline_manifest.py" --patches "$DEST/xnu/patches" \
        --expect-root "$BASELINE_MANIFEST_SHA256" --expect-count "$BASELINE_FILES"
fi

cp "$ROOT/patches/0080-ruby-ufs.patch" "$ROOT/patches/0084-ruby-autoswipe.patch" \
    "$ROOT/patches/0085-ruby-goodix-spi.patch" \
    "$ROOT/patches/0086-ruby-usb-p0.patch" \
    "$ROOT/patches/0087-ruby-usb-p2.patch" \
    "$ROOT/patches/0088-ruby-handoff-dump.patch" \
    "$ROOT/patches/0089-ruby-ep0-timing.patch" \
    "$ROOT/patches/0090-ruby-devspeed-hs.patch" \
    "$ROOT/patches/0091-ruby-devconf-offset.patch" \
    "$ROOT/patches/0092-ruby-config-endpoints.patch" \
    "$ROOT/patches/0093-ruby-poll-pid.patch" \
    "$ROOT/patches/0094-ruby-ep0-thread.patch" \
    "$ROOT/patches/0095-ruby-ep2-log.patch" \
    "$ROOT/patches/0096-ruby-ep2-ring-guard.patch" \
    "$ROOT/patches/0097-ruby-ep2-serialize.patch" \
    "$ROOT/patches/0098-ruby-ep2-state.patch" \
    "$ROOT/patches/0099-ruby-ep2-nozlp.patch" \
    "$ROOT/patches/0100-ruby-ep2-recover.patch" \
    "$ROOT/patches/0101-ruby-ep0-nodataend.patch" \
    "$ROOT/patches/0102-ruby-ep2-slot0.patch" \
    "$ROOT/patches/0103-ruby-ep0-reset.patch" \
    "$ROOT/patches/0104-ruby-ep0-p9-parity.patch" \
    "$ROOT/patches/0105-ruby-ep0-ack-fifo-drain.patch" \
    "$ROOT/patches/0106-ruby-ep0-ack-fast-drain.patch" \
    "$ROOT/patches/0107-ruby-ep0-p9-latency.patch" \
    "$ROOT/patches/0108-ruby-ep2-frame63.patch" \
    "$ROOT/patches/0109-ruby-ep2-slot2.patch" \
    "$ROOT/patches/0110-ruby-ep2-queue.patch" \
    "$ROOT/patches/0111-ruby-ep2-resume.patch" \
    "$ROOT/patches/0112-ruby-ep2-rx.patch" \
    "$ROOT/patches/0112b-ruby-ep2-rx-diag.patch" \
    "$ROOT/patches/0113-ruby-ep0-state-machine.patch" \
    "$ROOT/patches/0113b-ruby-ep0-dataend.patch" \
    "$ROOT/patches/0113c-ruby-ep0-tx-spin.patch" \
    "$ROOT/patches/0113d-ruby-ep0-dataend-tick.patch" \
    "$ROOT/patches/0114-ruby-usb-phy-detach.patch" \
    "$ROOT/patches/0116-ruby-usb-attach-retry.patch" \
    "$ROOT/patches/0119-ruby-usb-retry-watchdog.patch" \
    "$ROOT/patches/0120-ruby-ep0-log-read.patch" \
    "$ROOT/patches/0121-ruby-ep2-recover.patch" \
    "$ROOT/patches/0124-ruby-ep2-qisar0.patch" \
    "$ROOT/patches/0125-ruby-ep2-telemetry.patch" \
    "$ROOT/patches/0126a-ruby-ep2-drain.patch" \
    "$ROOT/patches/0126a2-ruby-ep2-map.patch" \
    "$ROOT/patches/0127-ruby-ep2-halt-clear.patch" \
    "$ROOT/patches/0128-ruby-ep2-ring16.patch" \
    "$ROOT/patches/0129a-ruby-ep2-cmd.patch" \
    "$ROOT/patches/0130-ruby-ep2-ring64.patch" \
    "$ROOT/patches/0131-ruby-reset-probe.patch" \
    "$ROOT/patches/0131b-ruby-probe-write.patch" \
    "$ROOT/patches/0140-ruby-ramdisk-import.patch" \
    "$ROOT/patches/0141-ruby-usb-decouple.patch" \
    "$ROOT/patches/0142-ruby-ep2-mps512.patch" \
    "$ROOT/patches/0143-ruby-ep2-frame511-rearm-drain.patch" \
    "$ROOT/patches/0144-ruby-probe-repl.patch" \
    "$ROOT/patches/0145-ruby-usb-enum-window.patch" \
    "$ROOT/patches/0146a-obs-ruby-ep2-log-off.patch" \
    "$ROOT/patches/0146a-qmu-ruby-usb-rearm-rx.patch" \
    "$ROOT/patches/0147-ruby-ep0-cmd.patch" \
    "$ROOT/patches/0148-ruby-pwrap-init.patch" \
    "$ROOT/patches/0149-ruby-keywatch.patch" \
    "$ROOT/patches/0150-ruby-keys.patch" \
    "$ROOT/patches/0152-ruby-reboot.patch" \
    "$ROOT/patches/0152b-ruby-reboot-psci.patch" \
    "$ROOT/patches/0154-ruby-battery.patch" \
    "$ROOT/patches/0155-ruby-i2c5-share.patch" \
    "$ROOT/patches/0156-ruby-found-ro.patch" \
    "$ROOT/patches/0156b-ruby-p24-battery.patch" \
    "$ROOT/patches/0157-ruby-hal.patch" \
    "$ROOT/patches/0158-ruby-i2c-hal.patch" \
    "$ROOT/patches/0159-ruby-eint-touch.patch" \
    "$ROOT/patches/0160-ruby-eint.patch" \
    "$ROOT/patches/0161-ruby-irq.patch" \
    "$ROOT/patches/0162-ruby-irq-adjudicate.patch" \
    "$ROOT/patches/0163-ruby-irq-enable.patch" \
    "$ROOT/patches/0164-ruby-eint-dom.patch" \
    "$ROOT/patches/0165-ruby-eint-demux.patch" \
    "$ROOT/patches/0166-ruby-eint-deferred.patch" \
    "$ROOT/patches/0167-ruby-gt-diag.patch" \
    "$ROOT/patches/0168-ruby-spi3-touch.patch" \
    "$ROOT/patches/0169-ruby-kpd-irq.patch" \
    "$ROOT/patches/0171-ruby-usb-hotplug.patch" \
    "$ROOT/patches/0172-ruby-usb-hotplug-diag.patch" \
    "$ROOT/patches/0173-ruby-usb-hotplug-ext.patch" \
    "$ROOT/patches/0174-ruby-usb-assist.patch" \
    "$ROOT/patches/0175-ruby-gic-kpd.patch" \
    "$ROOT/patches/0176-ruby-eint-b1.patch" \
    "$ROOT/patches/0177-ruby-eint-native-parent.patch" \
    "$ROOT/patches/0178-ruby-eint-child-oneshot.patch" \
    "$ROOT/patches/0179-ruby-eint-retry.patch" \
    "$ROOT/patches/0180-ruby-usb-qcr1-zlp.patch" \
    "$ROOT/patches/0181-ruby-usb-gpd-cache-order.patch" \
    "$ROOT/patches/0182-ruby-usb-gpd-dump.patch" \
    "$ROOT/patches/0183-ruby-usb-gpd-dump-halt.patch" \
    "$ROOT/patches/0184-ruby-usb-inflight16.patch" \
    "$ROOT/patches/0185-ruby-usb-phy-eye-noise.patch" \
    "$ROOT/patches/0186-ruby-usb-tx-slew.patch" \
    "$ROOT/patches/0187-ruby-usb-init-order.patch" \
    "$ROOT/patches/0188-ruby-usb-state-reset.patch" \
    "$ROOT/patches/0189-ruby-usb-state-start.patch" \
    "$ROOT/patches/0194-ruby-usb-golden-srctrl.patch" \
    "$ROOT/patches/0195-ruby-usb-acknowledgements.patch" \
    "$ROOT/patches/0196-ruby-usb-irq-ep0.patch" \
    "$ROOT/patches/0197-ruby-usb-qmu-irq.patch" \
    "$ROOT/patches/0198-ruby-ep2-pad-frames.patch" \
    "$ROOT/patches/0199-ruby-probe-clk-regions.patch" \
    "$ROOT/patches/0200-sweetfb-dbg-gate.patch" \
    "$ROOT/patches/0201-ruby-usb-gpd-stride16-apmixed.patch" \
    "$ROOT/patches/0202-ruby-usb-frame-watchdog.patch" \
    "$ROOT/patches/0203-ruby-usb-tphy-coldcycle.patch" \
    "$ROOT/patches/0204-ruby-usb-gpd-uc.patch" \
    "$ROOT/patches/0204b-ruby-usb-gpd-uc-alloc.patch" \
    "$ROOT/patches/0206b-ruby-usb-single-gpd.patch" \
    "$ROOT/patches/0207-ruby-usb-qcr0-off.patch" \
    "$ROOT/patches/0211-ruby-usb-ep1.patch" \
    "$ROOT/patches/0212-ruby-usb-ep1-qisar0.patch" \
    "$ROOT/patches/0213-ruby-usb-ep1-qisar1-fastpath.patch" \
    "$ROOT/patches/0214-ruby-usb-ep1-next-hwo-clear.patch" \
    "$ROOT/patches/0215-ruby-usb-ep1-len-passthrough.patch" \
    "$ROOT/patches/0216-ruby-usb-ep1-out-rx1.patch" \
    "$ROOT/patches/0217-ruby-usb-ep1-backpressure-counters.patch" \
    "$ROOT/patches/0218-ruby-usb-ep-layer.patch" \
    "$ROOT/patches/0219-ruby-usb-desc-order.patch" \
    "$ROOT/patches/0220-ruby-usb-qmu-init-order.patch" \
    "$ROOT/patches/0221-ruby-usb-xfer-1to1.patch" \
    "$ROOT/patches/0222-ruby-usb-xfer-workloop.patch" \
    "$ROOT/patches/0223-ruby-usb-func-framework.patch" \
    "$ROOT/patches/0224-ruby-usb-cdc-acm.patch" \
    "$ROOT/patches/0225-ruby-usb-cdc-acm-full.patch" \
    "$ROOT/patches/0226-ruby-usb-acm-real.patch" \
    "$ROOT/patches/0227-ruby-usb-ep0-out-ack.patch" \
    "$ROOT/patches/0228-ruby-usb-acm-out-rxpath.patch" \
    "$ROOT/patches/0229-ruby-usb-acm-isolation.patch" \
    "$ROOT/patches/0230-ruby-usb-acm-setup-ack.patch" \
    "$ROOT/patches/0231-ruby-usb-acm-echo.patch" \
    "$ROOT/patches/0232-ruby-usb-rx-irq.patch" \
    "$ROOT/patches/0233-ruby-usb-acm-diag.patch" \
    "$ROOT/patches/0234-ruby-usb-qmu-restart.patch" \
    "$ROOT/patches/0235-ruby-usb-qcr0-cs.patch" \
    "$ROOT/patches/0236-ruby-usb-qiesr0-rx.patch" \
    "$ROOT/patches/0237-ruby-usb-qiesr0-mask.patch" \
    "$ROOT/patches/0238-ruby-usb-resume-poll.patch" \
    "$ROOT/patches/0239-ruby-usb-full-restart.patch" \
    "$ROOT/patches/0240-ruby-usb-restart-diag.patch" \
    "$ROOT/patches/0241-ruby-usb-tx-retry.patch" \
    "$ROOT/patches/0242-ruby-usb-diag-decl.patch" \
    "$ROOT/patches/0243-ruby-usb-tx-watchdog.patch" \
    "$ROOT/patches/0244-ruby-usb-rx-watchdog.patch" \
    "$ROOT/patches/0245-ruby-usb-force-restart.patch" \
    "$ROOT/patches/0246-ruby-usb-cs-off.patch" \
    "$ROOT/patches/0247-ruby-usb-rx-resident.patch" \
    "$ROOT/patches/0248-ruby-usb-zero-chksum.patch" \
    "$ROOT/patches/0249-ruby-usb-cs-off-zero-chk.patch" \
    "$ROOT/patches/0251-ruby-usb-bit0-only.patch" \
    "$ROOT/patches/0252-ruby-usb-dir-cs.patch" \
    "$ROOT/patches/0253-ruby-usb-fifo-flush.patch" \
    "$ROOT/patches/0254-ruby-usb-fifo-full-force.patch" \
    "$ROOT/patches/0255-ruby-usb-vendor-zero-force.patch" \
    "$ROOT/patches/0256-ruby-usb-fix-printf-esc.patch" \
    "$ROOT/patches/0257-ruby-usb-rx-bits.patch" \
    "$ROOT/patches/0258-ruby-usb-fifo-base.patch" \
    "$ROOT/patches/0259-ruby-usb-slew4.patch" \
    "$DEST/xnu/patches/"
cp "$ROOT/patches/historical/0081-ruby-swap-debug.patch" \
    "$ROOT/patches/historical/0082-ruby-wifi-stub.patch" \
    "$ROOT/patches/historical/0083-ruby-iokit-match-trace.patch" \
    "$DEST/xnu/patches/"

# SKIP_PATCHES holds patch numbers (prefix match, e.g. "0144" or "0144 0143b").
# The matching patches are dropped again so the caller can build an older
# line from the same tree; it must then pass the matching PATCHSET_SHA256.
for skip in $SKIP_PATCHES; do
    for f in "$DEST/xnu/patches/${skip}"*.patch; do
        [ -e "$f" ] || continue
        echo "skipping patch: $(basename "$f")"
        rm -f "$f"
    done
done

git -C "$DEST" apply --whitespace=nowarn "$ROOT/ci/baseline-changes.patch"

"$PYTHON" "$ROOT/ci/normalize_lf.py" "$DEST/xnu/patches"

# Reject malformed diffs here.  The upstream build applies patches with GNU
# patch and can otherwise skip a corrupt file without failing (0170 did).
for p in "$DEST"/xnu/patches/*.patch; do
    if ! git -C "$DEST" apply --stat "xnu/patches/$(basename "$p")" \
        >/dev/null 2>&1; then
        echo "prepare-baseline: malformed patch: $(basename "$p")" >&2
        exit 6
    fi
done
actual_hash=$("$PYTHON" "$ROOT/ci/patchset_hash.py" "$DEST/xnu/patches")
echo "patchset: $actual_hash"

if [ "$actual_hash" != "$PATCHSET_SHA256" ]; then
    echo "prepare-baseline: patchset mismatch" >&2
    echo "  expected $PATCHSET_SHA256" >&2
    exit 5
fi

echo "baseline ready: $DEST"
