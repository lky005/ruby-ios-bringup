# Synthetic touch autoswipe

The authoritative implementation is `patches/0084-ruby-autoswipe.patch`. It is
a diff against the upstream `SweetHID.cpp`, not a copied source file.

It adds a boot-arg-gated `IOTimerEventSource` to the existing
`SweetHIDTouch` service. When armed, the timer calls the same
`SweetHIDTouch::touch(finger, down, x, y)` entry that a real touch driver is
expected to use, so the HID path can be tested before the Goodix driver
exists.

Boot arguments:

| Argument | Meaning | Example |
|---|---|---|
| `sweetautoswipe` | start delay in ms; 0 disables | `90000` |
| `sweetautoswiperetry` | delay between attempts in ms; minimum 1000 | `15000` |
| `sweetautoswipeattempts` | number of attempts; capped at 8 | `3` |

Each attempt starts at `y=2390` (inside the bottom-edge tip zone) and uses one
of three short/long/medium swipe profiles. On the author's device the third
attempt unlocked the lock screen to the home screen with normal animations.

This is **not** a real touch driver. It proves the
`SweetHIDTouch -> IOHIDEventService -> backboardd -> SpringBoard` path; a real
Goodix driver should feed coordinates into the same `touch()` function.
