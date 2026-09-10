# Experimental replacement firmware

This directory contains a compile-only AUKEY KM-G6 target for SMK revision
`2876de0684c1fb60af010ef0fb9426bb8951fb34`.

The target implements the GPIO matrix and LED PWM topology recovered from the
verified stock firmware. Its full-size ISO keymap is decoded from stock feature
report `0x09`; the host operating system's Italian layout provides the printed
Italian characters. Auxiliary LEDs, USB behavior, and recovery have not yet
passed the tests required for flashing real hardware.

Run `firmware/build-smk.sh` to clone the pinned SMK revision, apply the target
patch, and compile it in a Debian Trixie container with SDCC 4.5. The script
does not access or write the keyboard.

The active-low LED-row correction produces SHA-256
`c9045ecd9cfe89b82af7ab8de0d65093fbde466ae243ca00c5332584e3cd0a6b`.
SMK's interrupt checker reported all 14 vectors claimed and no ISR overlay
collisions.

This revision includes the version-1 host-lighting protocol described in
`docs/PROTOCOL.md` and a 126-byte intensity framebuffer. The `km-g6-frame`
host utility is built by the project's normal `make` command.

**Do not flash the generated image yet.** A successful compile proves source
and interrupt-layout consistency, not correct electrical or runtime behavior.

## Guarded write and restore commands

`firmware/check-readiness.sh` performs only local, read-only checks. The two
write scripts require explicit acknowledgement flags and verify pinned hashes
before invoking sinowisp:

```text
sudo firmware/flash-experimental.sh --yes-i-accept-brick-risk
sudo firmware/restore-stock.sh --restore-verified-stock
```

Do not run the flash command merely because it exists. PC-only restoration
requires the application to initialize USB and accept report `0x05`. Analysis
found no verified power-on key combination that enters the untouched
bootloader when the application cannot run.
