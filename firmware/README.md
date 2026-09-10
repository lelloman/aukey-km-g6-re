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

The active-high LED-row correction produces SHA-256
`90291d167332047ab114be5a467f48cdad6f1b6d72ee59a4ae9a76929be0915b`.
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
