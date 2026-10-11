# Experimental replacement firmware

This directory contains an experimental AUKEY KM-G6 target for SMK revision
`2876de0684c1fb60af010ef0fb9426bb8951fb34`.

The target implements the GPIO matrix and LED PWM topology recovered from the
verified stock firmware. Its full-size ISO keymap is decoded from stock feature
report `0x09`; the host operating system's Italian layout provides the printed
Italian characters. The user has tested typing, per-key brightness and lock
indicators. USB behavior and recovery are not comprehensively validated.

## From a fresh clone

Requirements: Linux, `sudo`, git, python3, a C compiler, Docker, Rust 1.88+
(cargo), and network access for the first build. Then:

```sh
firmware/build-smk.sh          # firmware image (Docker); never touches the keyboard
firmware/build-sinowisp.sh     # pinned flasher; run without sudo
sudo firmware/backup-stock.sh  # once, while the keyboard still runs stock firmware
firmware/check-readiness.sh    # local checks only
sudo firmware/flash-experimental.sh --yes-i-accept-brick-risk
```

`build-smk.sh` clones the pinned SMK revision, applies the target patch, runs
the host regression tests, and compiles in a digest-pinned Debian Trixie
container whose packages (SDCC 4.5.0, meson 1.7.0) come from a fixed
snapshot.debian.org date, so the output matches the hash pinned in
`flash-experimental.sh`. `build-sinowisp.sh` clones sinowisp at a pinned
commit into `firmware/build/sinowisp`, which persists across reboots.

`backup-stock.sh` reads the full 64 KiB flash twice (replug the keyboard
between reads), refuses to continue if the reads differ, extracts the 60 KiB
application region (the first 61440 bytes) for `restore-stock.sh`, and records
both hashes in `hardware/backups/SHA256SUMS`. It reports whether the dump
matches the reference KM-G6 stock dump. It refuses to overwrite existing
backups or to run when the keyboard already reports SMK. Note that even a read
may touch flash metadata (see the top-level README); copy the backups to
another disk before flashing.

The patch builds `firmware/build/aukey-km-g6_stock-pwm-candidate.hex`, using
the traced stock control bytes and column-before-row ordering. It is the only
image the flash command writes; `--stock-pwm-candidate` is still accepted for
old commands. See [the brightness audit](../docs/BRIGHTNESS-AUDIT.md#stock-pwm-candidate-implementation)
for validation and remaining timing limitations.

The candidate also implements stock's active-low Num/Caps/Scroll Lock
indicators on P0.2/P0.3/P0.4, with output direction and pull-ups enabled.
Run `python3 firmware/test-lock-indicators.py` for host-side logic checks.
The user reports working lock indicators and visible brightness control
across 0–255; Scroll Lock has not been separately confirmed.

The candidate also restores **Fn+F10** (volume down) and **Fn+F11**
(volume up) using standard USB consumer reports. F10/F11 without Fn retain
their normal behavior; all other Fn-layer positions remain transparent.
The original volume update could leave volume repeating when Fn was released
before F10/F11: the release was resolved on the base layer, leaving the consumer
key held. The matrix now remembers each pressed keycode until its release, and
releasing Fn preserves unrelated held keys. The build runs a host regression
test for both volume keys and both release orders, plus base-key presses across
Fn changes. That image had SHA-256
`7d6946742519bcfba783049e5072b640a3c09034bb1c23709f6fc9af2fd83e80`.

That image could emit short bursts of a character (seen on M and Enter): its
only debounce was two row samples 10 µs apart, while switch contacts bounce for
milliseconds and the matrix is scanned roughly every 0.8 ms. The scan now
publishes the raw matrix only after it has been stable for 6 consecutive scans
(about 5 ms, QMK's default global deferred debounce). `firmware/test-debounce.py`
fails on the previous scan code and passes with the fix. On 2026-10-11 the
user flashed this image and confirmed on hardware that the repeated characters
are gone and the Fn+F10/F11 volume keys work. Its SHA-256 is
`7dd6dada98cc4c5bd846ba496e362f3a418918a1eeae5843aedc9ab907a2065f`.

The active-low LED-row correction produces SHA-256
`3357372b13a94605b2717ce0ff391144434bd2bcc6feaf22a78fae3922c00fad`.
SMK's interrupt checker reported all 14 vectors claimed and no ISR overlay
collisions.

This revision includes the version-1 host-lighting protocol described in
`docs/PROTOCOL.md` and a 126-byte intensity framebuffer. The `km-g6-frame`
host utility is built by the project's normal `make` command.

**The candidate remains experimental.** Visual testing does not establish
electrical safety, stock-equivalent maximum brightness or reliable recovery.

## Guarded write and restore commands

`firmware/check-readiness.sh` performs only local, read-only checks. The two
write scripts require explicit acknowledgement flags and verify pinned hashes
before invoking sinowisp:

```text
firmware/flash-experimental.sh --yes-i-accept-brick-risk --dry-run
sudo firmware/flash-experimental.sh --yes-i-accept-brick-risk
sudo firmware/restore-stock.sh --restore-verified-stock
```

Unknown arguments are rejected. `--dry-run` checks the image hash and the
stock backup against `hardware/backups/SHA256SUMS` without requiring sinowisp
or touching a device. The write scripts need `sudo` because the keyboard's
hidraw devices are root-only; without it sinowisp reports "Device not found".

Do not run the flash command merely because it exists. PC-only restoration
requires the application to initialize USB and accept report `0x05`. Analysis
found no verified power-on key combination that enters the untouched
bootloader when the application cannot run.
