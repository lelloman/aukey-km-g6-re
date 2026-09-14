# Experimental replacement firmware

This directory contains an experimental AUKEY KM-G6 target for SMK revision
`2876de0684c1fb60af010ef0fb9426bb8951fb34`.

The target implements the GPIO matrix and LED PWM topology recovered from the
verified stock firmware. Its full-size ISO keymap is decoded from stock feature
report `0x09`; the host operating system's Italian layout provides the printed
Italian characters. The user has tested typing, per-key brightness and lock
indicators. USB behavior and recovery are not comprehensively validated.

Run `firmware/build-smk.sh` to clone the pinned SMK revision, apply the target
patch, and compile it in a Debian Trixie container with SDCC 4.5. The script
does not access or write the keyboard.

The current patch builds a separate stock-PWM candidate at
`firmware/build/aukey-km-g6_stock-pwm-candidate.hex`, using the traced stock
control bytes and column-before-row ordering. It does not overwrite the
previous working default image. The guarded flash command defaults to the
previous image; `--stock-pwm-candidate` explicitly selects the separately
hash-pinned candidate. See [the brightness audit](../docs/BRIGHTNESS-AUDIT.md#stock-pwm-candidate-implementation)
for the candidate hash, validation and remaining timing limitations.

The candidate also implements stock's active-low Num/Caps/Scroll Lock
indicators on P0.2/P0.3/P0.4, with output direction and pull-ups enabled.
Run `python3 firmware/test-lock-indicators.py` for host-side logic checks.
The user reports working lock indicators and visible brightness control
across 0–255; Scroll Lock has not been separately confirmed.

The candidate also restores **Fn+F10** (volume down) and **Fn+F11**
(volume up) using standard USB consumer reports. F10/F11 without Fn retain
their normal behavior; all other Fn-layer positions remain transparent.
This update builds and passes host-side keymap/consumer-code checks, but
the volume shortcuts have not yet been tested on hardware. Its SHA-256 is
`f75ae815d3b578b6e348886e8ff23dd65983776bab164283673f3ad43ea50d2d`.

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
sudo firmware/flash-experimental.sh --yes-i-accept-brick-risk
sudo firmware/restore-stock.sh --restore-verified-stock
```

To explicitly test the stock-PWM candidate, first verify without accessing
the keyboard, then flash only if accepting the recovery risk below:

```sh
firmware/flash-experimental.sh --stock-pwm-candidate --yes-i-accept-brick-risk --dry-run
sudo firmware/flash-experimental.sh --stock-pwm-candidate --yes-i-accept-brick-risk
```

Unknown arguments are rejected. `--dry-run` checks the selected image and
stock recovery hashes without requiring sinowisp or touching a device.

Do not run the flash command merely because it exists. PC-only restoration
requires the application to initialize USB and accept report `0x05`. Analysis
found no verified power-on key combination that enters the untouched
bootloader when the application cannot run.
