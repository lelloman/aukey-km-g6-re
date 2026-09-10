# Controller research

## What is known

- USB identity: `258a:002a SINO WEALTH Gaming KB`
- Tested USB device revision: `10.36`
- Two HID interfaces, with vendor feature reports on interface 1
- The stock keyboard has one fixed-color LED per key, not independently
  color-selectable RGB LEDs
- The keyboard has onboard custom profiles but no official configuration
  software

## Controller identification

The controller package is marked `BYK901`, with secondary codes `NLA25` and
`1918`, and is an LQFP64 device. Current `sinowisp` and SMK device data identify
BYK901 as a label used for the Sino Wealth SH68F90A. The official SH68F90A
specification confirms a matching LQFP64 package, 64 KiB Flash, USB, and an
8051-compatible core.

The PCB is marked `KM-G6 UK B2 V1.1` and `20180529`. A six-pad footprint marked
`J4` sits beside the controller. Its visible lower labels include `TMS`, `TDI`,
and `TCK`, consistent with the SH68F90A ICP interface; the upper labels are
obscured in the photographs and must not be assigned without continuity
measurements or a clearer view.

The USB ID is reused across products, so it still cannot establish this
keyboard's bootloader image, code options, matrix wiring, LED wiring, or ISP
entry configuration.

## Why we are not dumping firmware yet

The `sinowisp` documentation states that a read operation can set an LJMP
opcode at `<firmware_size-5>`. That address depends on choosing the correct
platform and flash geometry. Therefore a guessed "read-only" dump is not
strictly non-mutating and is inappropriate before hardware identification.

Even after identification, replacement firmware should not be tested without
a recovery plan. The SMK project warns that firmware unable to return to ISP
mode can brick the device and recommends a stock dump plus a physical
programming method.

## Stock backup

On 2026-09-10, two full 64 KiB reads made with the SH68F90 platform geometry
(60 KiB application, 4 KiB bootloader, 2 KiB pages) were byte-for-byte
identical. The full-image SHA-256 is
`cf2dcfe9b6830e254d031eaeefc8c6974d602a10b0a4c80b95f329ead7a258f5`.
The bootloader MD5 is `2d169670eae0d36eae8188562c1f66e8`, which matches a
bootloader recognized by sinowisp for SH68F90/SH68F90A devices. The keyboard
requires a manual USB power cycle after an ISP session; the software reboot
command does not restore normal operation on this board.

## Useful sources

- [Official AUKEY KM-G6 manual](https://images.aukey.com/en/downloads/20190521192618-KM-G6_User_Manual.pdf)
- [Exact KM-G6 teardown/modification video](https://www.youtube.com/watch?v=Q3IOGxfu5AY)
- [sinowisp flash/ISP utility and device database](https://github.com/carlossless/sinowisp)
- [Official SH68F90A product page and datasheet](https://www.sinowealth.com/detaile?pro_id=308)
- [SMK replacement firmware for Sino Wealth 8051 keyboards](https://github.com/carlossless/smk)
- [sinodude physical programmer](https://github.com/carlossless/sinodude)
- [OpenRGB Sino Wealth controller source](https://gitlab.com/CalcProgrammer1/OpenRGB)
- [KM-G6 hardware and lighting review](https://www.tomshardware.com/reviews/aukey-km-g6-keyboard)

## Remaining evidence needed

- LED driver or shift-register markings
- Controller and LED-driver pin traces visible in photographs
- Complete J4 pad labels and continuity to MCU/power pins
- Stock code options, bootloader identity, and verified flash backup
