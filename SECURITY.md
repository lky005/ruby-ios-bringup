# Security

This is an experimental bring-up. It disables or bypasses several security
mechanisms (AMFI, sandbox, code signing, data protection) to run an unmodified
iOS userland on non-Apple hardware. Do not use it on a device that holds
personal data.

The repository does not contain Apple firmware, device dumps, signing keys or
credentials. Do not add them.

Report a problem by opening a GitHub security advisory or a minimal issue. Do
not include device serials, IMEI, MAC addresses, Apple account data or full
boot logs in an issue.

## Repository and CI hardening

- GitHub Actions are pinned by commit SHA; the workflow has
  `permissions: contents: read`.
- The Xcode version is a workflow input (default 16.0); runner, Xcode, SDK and
  brew versions are recorded in the run provenance.
- Enable 2FA on the hosting account. A private repository is not a backup.
- Do not add secrets, tokens, device dumps, root images or full logs.
- Media must be sanitized per `media/CAPTURE.md` before it is committed.
