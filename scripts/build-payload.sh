#!/bin/sh
# Build a SWEETXNU payload from a kernel + external ADT + cmdline.
#
# The upstream tools are fetched at a pinned commit; no upstream tree is
# vendored. The kernel, ADT and cmdline are supplied by the caller. The shim
# and ADT are NOT in this repository.
#
#   sh scripts/build-payload.sh \
#     --kernel <kernel.development.sweet> --adt <adt> \
#     --cmdline-file config/0085-boot.cmdline --out <payload.bin> \
#     [--base-dir <prepared-topaz>] [--expect-sha <sha256>]
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BASE_REPO=${BASE_REPO:-https://github.com/MakrSas/ios-topaz.git}
BASE_SHA=${BASE_SHA:-5095ac19dbdcf37b64b81fe443f4027ad51b84bf}
PYTHON=${PYTHON:-python3}

KERNEL=
ADT=
CMDLINE="$ROOT/config/0084-boot.cmdline"
OUT=
BASE_DIR=
EXPECT=
EXPECT_KERNEL=
EXPECT_ADT=

while [ "$#" -gt 0 ]; do
    case "$1" in
        --kernel) KERNEL=$2; shift 2 ;;
        --adt) ADT=$2; shift 2 ;;
        --cmdline-file) CMDLINE=$2; shift 2 ;;
        --out) OUT=$2; shift 2 ;;
        --base-dir) BASE_DIR=$2; shift 2 ;;
        --expect-sha) EXPECT=$2; shift 2 ;;
        --expect-kernel-sha) EXPECT_KERNEL=$2; shift 2 ;;
        --expect-adt-sha) EXPECT_ADT=$2; shift 2 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

[ -n "$KERNEL" ] && [ -n "$ADT" ] && [ -n "$OUT" ] || {
    echo "usage: build-payload.sh --kernel K --adt A --out P [--cmdline-file C] [--base-dir D] [--expect-sha S]" >&2
    exit 2
}
[ -f "$KERNEL" ] || { echo "missing kernel: $KERNEL" >&2; exit 3; }
[ -f "$ADT" ] || { echo "missing ADT: $ADT" >&2; exit 3; }
[ -f "$CMDLINE" ] || { echo "missing cmdline: $CMDLINE" >&2; exit 3; }

hash_file() {
    "$PYTHON" -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"
}
if [ -n "$EXPECT_KERNEL" ] && [ "$(hash_file "$KERNEL")" != "$EXPECT_KERNEL" ]; then
    echo "kernel sha256 mismatch" >&2; exit 3
fi
if [ -n "$EXPECT_ADT" ] && [ "$(hash_file "$ADT")" != "$EXPECT_ADT" ]; then
    echo "ADT sha256 mismatch" >&2; exit 3
fi

CLEANUP=
if [ -z "$BASE_DIR" ]; then
    BASE_DIR=$(mktemp -d)
    CLEANUP=1
    git init -q "$BASE_DIR"
    git -C "$BASE_DIR" remote add origin "$BASE_REPO"
    git -C "$BASE_DIR" fetch -q --depth 1 origin "$BASE_SHA"
    git -C "$BASE_DIR" checkout -q FETCH_HEAD
    actual=$(git -C "$BASE_DIR" rev-parse HEAD)
    [ "$actual" = "$BASE_SHA" ] || {
        echo "baseline mismatch: $actual" >&2
        exit 4
    }
fi

TOOL="$BASE_DIR/tools/mkpayload.py"
[ -f "$TOOL" ] || { echo "missing upstream tool: $TOOL" >&2; exit 5; }

CMDLINE_TEXT=$(cat "$CMDLINE")
# The SWEETXNU payload header stores 608 bytes including the NUL.
CMDLINE_LEN=$(printf '%s' "$CMDLINE_TEXT" | wc -c | tr -d ' ')
if [ "$CMDLINE_LEN" -gt 607 ]; then
    echo "cmdline too long: $CMDLINE_LEN bytes (max 607)" >&2
    exit 3
fi

"$PYTHON" "$TOOL" "$KERNEL" "$ADT" "$OUT" --cmdline "$CMDLINE_TEXT"

HASH=$(hash_file "$OUT")
echo "payload: $OUT"
echo "sha256 : $HASH"
if [ -n "$EXPECT" ] && [ "$HASH" != "$EXPECT" ]; then
    echo "payload sha256 mismatch: expected $EXPECT" >&2
    exit 6
fi

if [ -n "$CLEANUP" ]; then
    rm -rf "$BASE_DIR"
fi
