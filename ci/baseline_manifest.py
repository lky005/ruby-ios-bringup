#!/usr/bin/env python3
"""Verify a baseline patch set against its normalized manifest root.

The root is computed exactly like ci/patchset_hash.py: every .patch/.sh file is
normalized to LF, hashed, and the sorted "<sha256>  <name>" lines are hashed
again. Only .patch/.sh files participate.

    baseline_manifest.py --patches DIR --expect-root HEX [--expect-count N]
                         [--manifest FILE]
    baseline_manifest.py --self-test
"""
import argparse
import hashlib
import os
import sys
import tempfile


def normalize(data):
    return data.replace(b"\r\n", b"\n")


def digest_dir(root):
    names = sorted(
        name for name in os.listdir(root)
        if os.path.isfile(os.path.join(root, name))
        and (name.endswith(".patch") or name.endswith(".sh"))
    )
    lines = []
    for name in names:
        data = normalize(open(os.path.join(root, name), "rb").read())
        lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}\n")
    return names, lines, hashlib.sha256("".join(lines).encode()).hexdigest()


def fail(msg):
    print(f"baseline-manifest: {msg}", file=sys.stderr)
    raise SystemExit(3)


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "a.patch"), "wb").write(b"x\r\ny\n")
        open(os.path.join(tmp, "b.sh"), "wb").write(b"#!/bin/sh\n")
        open(os.path.join(tmp, "ignore.txt"), "wb").write(b"no\n")
        names, lines, root = digest_dir(tmp)
        if names != ["a.patch", "b.sh"]:
            fail(f"self-test names: {names}")
        expected_a = hashlib.sha256(b"x\ny\n").hexdigest()
        if lines[0] != f"{expected_a}  a.patch\n":
            fail("self-test CRLF normalization failed")
        expected_root = hashlib.sha256("".join(lines).encode()).hexdigest()
        if root != expected_root:
            fail("self-test root is not the hash of the lines")
    print("baseline-manifest: self-test ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patches")
    ap.add_argument("--expect-root")
    ap.add_argument("--expect-count", type=int)
    ap.add_argument("--manifest")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.patches:
        ap.error("--patches is required unless --self-test")

    names, lines, root = digest_dir(args.patches)
    if args.expect_count is not None and len(names) != args.expect_count:
        fail(f"file count {len(names)} != {args.expect_count}")
    if args.expect_root and root != args.expect_root.lower():
        fail(f"root {root} != {args.expect_root.lower()}")
    if args.manifest:
        recorded = [
            line.rstrip("\r")
            for line in open(args.manifest, "r", encoding="utf-8").read().split("\n")
            if line.strip()
        ]
        if recorded != [line.rstrip("\n") for line in lines]:
            fail(f"manifest mismatch at {args.manifest}")
    print(f"baseline: files={len(names)} root={root}")


if __name__ == "__main__":
    main()
