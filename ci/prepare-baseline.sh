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
PATCHSET_SHA256=${PATCHSET_SHA256:-27894e7b274ea57131b5ee57799eb13c1ca2ddd7a6d9e38c15468cdd0dd55ce9}
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
    "$DEST/xnu/patches/"
cp "$ROOT/patches/historical/0081-ruby-swap-debug.patch" \
    "$ROOT/patches/historical/0082-ruby-wifi-stub.patch" \
    "$ROOT/patches/historical/0083-ruby-iokit-match-trace.patch" \
    "$DEST/xnu/patches/"

git -C "$DEST" apply --whitespace=nowarn "$ROOT/ci/baseline-changes.patch"

"$PYTHON" "$ROOT/ci/normalize_lf.py" "$DEST/xnu/patches"
actual_hash=$("$PYTHON" "$ROOT/ci/patchset_hash.py" "$DEST/xnu/patches")
echo "patchset: $actual_hash"

if [ "$actual_hash" != "$PATCHSET_SHA256" ]; then
    echo "prepare-baseline: patchset mismatch" >&2
    echo "  expected $PATCHSET_SHA256" >&2
    exit 5
fi

echo "baseline ready: $DEST"
