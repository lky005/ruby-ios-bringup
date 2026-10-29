#!/usr/bin/env python3
"""Host-side checks for this repository. No device and no image writes.

Checks:
  * Python syntax for every .py file
  * shell syntax for every .sh file (if sh is available)
  * synthetic 4K ICL round-trip (dry-run, apply, negative case)
  * optional: real ICL block round-trip (--icl-orig/--icl-patched)
  * optional: patch apply checks against an existing XNU tree (--xnu-tree)
  * optional: boot image layout dump (--boot-image)
  * forbidden binary/media extensions
  * personal-path and secret patterns

Exit code is non-zero only for hard failures. External-tree checks are
informational because the tree state depends on which upstream patches have
already been applied.
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
FORBIDDEN_EXT = {
    ".img", ".bin", ".elf", ".o", ".a", ".dtb", ".dtbo", ".dmg", ".ipsw",
    ".zip", ".7z", ".tar", ".gz", ".jpg", ".jpeg", ".png", ".mp4", ".mov",
}
MEDIA_ALLOW = {
    "media/autoswipe.mp4",
    "media/home-screen.jpg",
}
TEXT_EXT = {
    ".md", ".py", ".sh", ".c", ".h", ".cpp", ".S", ".ld", ".patch", ".diff",
    ".txt", ".yml", ".yaml", ".env", ".cmdline", ".gitignore", ".gitattributes",
}
PII_PATTERNS = [
    (re.compile(r"C:\\\\Users\\\\", re.I), "personal Windows path"),
    (re.compile(r"D:\\\\ios-ruby-work", re.I), "personal work path"),
    (re.compile("gh" + r"p_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile("github_" + "pat_"), "GitHub token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS key"),
    (re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"), "private key"),
    (re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"), "email address"),
    (re.compile(r"\blky005\b", re.I), "personal GitHub handle"),
]

# The two project URLs are public; the bare handle elsewhere is still flagged.
PROJECT_URLS = {
    "https://github.com/lky005/ruby-ios-bringup",
    "https://github.com/lky005/ruby-ios-probes",
}

hard_failures = []
warnings = []


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def fail(msg):
    hard_failures.append(msg)
    print(f"FAIL  {msg}")


def ok(msg):
    print(f"ok    {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"warn  {msg}")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def walk_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Skip local-only, gitignored data.
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "private")]
        for name in filenames:
            yield os.path.join(dirpath, name)


def check_python():
    count = 0
    for path in walk_files():
        if not path.endswith(".py"):
            continue
        count += 1
        result = run([PY, "-m", "py_compile", path])
        if result.returncode != 0:
            fail(f"python syntax: {os.path.relpath(path, ROOT)}: {result.stderr.strip()}")
    if count:
        ok(f"python syntax ({count} files)")


def check_shell():
    if not shutil.which("sh"):
        warn("sh not found; skipping shell syntax")
        return
    count = 0
    for path in walk_files():
        if not path.endswith(".sh"):
            continue
        count += 1
        result = run(["sh", "-n", path])
        if result.returncode != 0:
            fail(f"shell syntax: {os.path.relpath(path, ROOT)}: {result.stderr.strip()}")
    if count:
        ok(f"shell syntax ({count} files)")


def check_forbidden_files():
    found = []
    allowed = []
    for path in walk_files():
        ext = os.path.splitext(path)[1].lower()
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if ext in FORBIDDEN_EXT:
            if rel in MEDIA_ALLOW:
                allowed.append(rel)
            else:
                found.append(rel)
    if found:
        fail("forbidden binary/media files: " + ", ".join(found))
    else:
        suffix = f" (allowlisted media: {len(allowed)})" if allowed else ""
        ok("no forbidden binary/media files" + suffix)


def check_pii():
    hits = []
    for path in walk_files():
        ext = os.path.splitext(path)[1].lower()
        if ext not in TEXT_EXT and os.path.basename(path) not in (".gitignore", ".gitattributes"):
            continue
        try:
            text = open(path, "r", encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for url in PROJECT_URLS:
            text = text.replace(url, "")
        for pattern, label in PII_PATTERNS:
            for match in pattern.finditer(text):
                hits.append(f"{os.path.relpath(path, ROOT)}: {label}: {match.group(0)}")
    if hits:
        for hit in hits:
            fail("pii/secret: " + hit)
    else:
        ok("no personal paths or secret patterns")


def check_markdown_links():
    missing = []
    for path in walk_files():
        if not path.endswith(".md"):
            continue
        text = open(path, "r", encoding="utf-8", errors="ignore").read()
        for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(resolved):
                missing.append(f"{os.path.relpath(path, ROOT)} -> {target}")
    if missing:
        for item in missing:
            fail("markdown link: " + item)
    else:
        ok("markdown links")


def check_synthetic_icl():
    tool = os.path.join(ROOT, "tools", "image", "icl_nop.py")
    with tempfile.TemporaryDirectory() as tmp:
        block = bytearray(4096)
        block[0xF0C:0xF0C + 4] = bytes.fromhex("02255e95")
        block_path = os.path.join(tmp, "block.bin")
        out_path = os.path.join(tmp, "out.bin")
        open(block_path, "wb").write(block)
        expected = bytearray(block)
        expected[0xF0C:0xF0C + 4] = bytes.fromhex("1f2003d5")
        expected = bytes(expected)

        dry = run([PY, tool, "--input-block", block_path,
                   "--expect-block-sha", sha256(bytes(block)),
                   "--expect-patched-sha", sha256(expected)])
        if dry.returncode != 0:
            fail("icl dry-run failed: " + dry.stderr.strip())
            return

        applied = run([PY, tool, "--input-block", block_path,
                       "--expect-block-sha", sha256(bytes(block)),
                       "--expect-patched-sha", sha256(expected),
                       "--output", out_path, "--apply"])
        if applied.returncode != 0:
            fail("icl apply failed: " + applied.stderr.strip())
            return
        if open(out_path, "rb").read() != expected:
            fail("icl output bytes differ from the expected patch")
            return
        if open(block_path, "rb").read() != bytes(block):
            fail("icl modified the input block")
            return

        negative = run([PY, tool, "--input-block", block_path,
                        "--expect-bytes", "00000000",
                        "--output", os.path.join(tmp, "bad.bin"), "--apply"])
        if negative.returncode == 0:
            fail("icl accepted a wrong --expect-bytes")
            return
    ok("synthetic ICL round-trip (dry-run, apply, negative case)")


def check_real_icl(orig_path, patched_path):
    tool = os.path.join(ROOT, "tools", "image", "icl_nop.py")
    orig = open(orig_path, "rb").read()
    patched = open(patched_path, "rb").read()
    if len(orig) != 4096 or len(patched) != 4096:
        fail("real ICL blocks must be exactly 4096 bytes")
        return
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "patched.bin")
        result = run([PY, tool, "--input-block", orig_path,
                      "--expect-block-sha", sha256(orig),
                      "--expect-patched-sha", sha256(patched),
                      "--output", out_path, "--apply"])
        if result.returncode != 0:
            fail("real ICL round-trip failed: " + result.stderr.strip())
            return
        if open(out_path, "rb").read() != patched:
            fail("real ICL output does not match the recorded patched block")
            return
    ok(f"real ICL round-trip ({sha256(orig)[:12]} -> {sha256(patched)[:12]})")


def check_patches(xnu_tree):
    patch_dir = os.path.join(ROOT, "patches")
    checks = [
        ("0081-ruby-swap-debug.patch", False),
        ("0083-ruby-iokit-match-trace.patch", False),
        ("0084-ruby-autoswipe.patch", False),
        ("0080-ruby-ufs.patch", True),
        ("0082-ruby-wifi-stub.patch", True),
    ]
    for name, reverse in checks:
        path = os.path.join(patch_dir, "historical", name)
        if not os.path.exists(path):
            path = os.path.join(patch_dir, name)
        cmd = ["git", "apply", "--check"]
        if reverse:
            cmd.append("--reverse")
        cmd.append(path)
        result = run(cmd, cwd=xnu_tree)
        label = "reverse" if reverse else "apply"
        if result.returncode == 0:
            ok(f"patch {name} ({label}) on {xnu_tree}")
        else:
            warn(f"patch {name} ({label}) did not pass on this tree: "
                 f"{result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'unknown'}")


def read_env(path):
    values = {}
    for line in open(path, "r", encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def check_ci_pins(config_path):
    env_path = config_path if os.path.isabs(config_path) else os.path.join(ROOT, config_path)
    rel_env = os.path.relpath(env_path, ROOT)
    wf_path = os.path.join(ROOT, ".github", "workflows", "xnu.yml")
    changes_path = os.path.join(ROOT, "ci", "baseline-changes.patch")
    recipe_path = os.path.join(ROOT, "ci", "prepare-baseline.sh")
    remove_path = os.path.join(ROOT, "ci", "topaz-patches-to-remove.txt")
    delta_path = os.path.join(ROOT, "ci", "ruby-baseline.diff")

    required = (env_path, wf_path, changes_path, recipe_path, remove_path)
    if not all(os.path.exists(p) for p in required):
        fail(f"missing {rel_env}, workflow or recipe files")
        return
    if os.path.exists(delta_path):
        fail("ci/ruby-baseline.diff is present; option B requires the recipe only")
        return

    pins = read_env(env_path)
    workflow = open(wf_path, "r", encoding="utf-8").read()
    missing = []
    for key in ("BASELINE_MANIFEST_SHA256", "PATCHSET_SHA256", "DXB_REPO",
                "DXB_SHA", "MACOS_VERSION", "KERNEL_CONFIG", "MACHINE_CONFIG"):
        value = pins.get(key)
        if value and value not in workflow:
            missing.append(f"{key}={value}")
    if missing:
        fail("workflow does not contain pins: " + ", ".join(missing))
        return

    # Artifact pins are required only once a booted reference exists.
    if pins.get("KERNEL_EXPECT_EXEC_DATA"):
        for key in ("CI_KERNEL_SHA256", "CI_KERNEL_EXEC_DATA_SHA256",
                    "CI_IMAGE_SHA256", "BOOT_CMDLINE"):
            if not pins.get(key):
                fail(f"{rel_env} is missing {key}")
                return
        if pins["CI_KERNEL_EXEC_DATA_SHA256"] != pins["KERNEL_EXPECT_EXEC_DATA"]:
            fail("KERNEL_EXPECT_EXEC_DATA and CI_KERNEL_EXEC_DATA_SHA256 differ")
            return

    cmdline_ref = pins.get("BOOT_CMDLINE")
    if cmdline_ref:
        cmdline_path = os.path.join(ROOT, cmdline_ref)
        if not os.path.exists(cmdline_path):
            fail(f"missing cmdline file: {cmdline_ref}")
            return

    actual = sha256(open(changes_path, "rb").read())
    expected = pins.get("BASELINE_CHANGES_SHA256", "").lower()
    if expected and actual != expected:
        fail(f"baseline-changes sha256 {actual} != {expected}")
        return
    if not expected:
        warn(f"BASELINE_CHANGES_SHA256 is not set in {rel_env}")

    if "prepare-baseline.sh" not in workflow:
        fail("workflow does not call ci/prepare-baseline.sh")
        return
    if "ruby-baseline.diff" in workflow or "RUBY_TREE" in workflow:
        fail("workflow still references the old delta/tree gate")
        return

    ok("CI pins, recipe and bundle config")


def check_boot(image):
    tool = os.path.join(ROOT, "tools", "image", "boot_verify.py")
    result = run([PY, tool, image])
    if result.returncode != 0:
        fail("boot_verify failed: " + result.stderr.strip())
        return
    print(result.stdout.rstrip())
    ok("boot image layout dump")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xnu-tree", help="existing patched XNU build tree")
    ap.add_argument("--boot-image", help="boot image to inspect (read-only)")
    ap.add_argument("--icl-orig", help="original 4K ICL block (read-only)")
    ap.add_argument("--icl-patched", help="expected patched 4K block (read-only)")
    ap.add_argument("--ci-config", default="config/0140.env",
                    help="branch config with the CI pins (default: config/0140.env)")
    args = ap.parse_args()

    print(f"root: {ROOT}")
    check_python()
    check_shell()
    check_forbidden_files()
    check_pii()
    check_ci_pins(args.ci_config)
    check_markdown_links()
    check_synthetic_icl()
    if args.icl_orig and args.icl_patched:
        check_real_icl(args.icl_orig, args.icl_patched)
    if args.xnu_tree:
        check_patches(os.path.abspath(args.xnu_tree))
    if args.boot_image:
        check_boot(args.boot_image)

    print()
    if hard_failures:
        print(f"FAILED: {len(hard_failures)} hard failure(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS: 0 hard failures, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
