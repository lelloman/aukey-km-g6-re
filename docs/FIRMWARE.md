# Stock firmware analysis

These notes describe the verified 60 KiB application image captured on
2026-09-10. Addresses are 8051 code addresses. Conclusions marked "likely"
still require confirmation before they are used in replacement firmware.

## Image layout

- Application: `0x0000`-`0xEFFF` (60 KiB)
- USB ISP bootloader: `0xF000`-`0xFFFF` (4 KiB)
- Reset vector: `LJMP 0x54FD`
- C runtime initialization: `0x54FD`
- Main entry after runtime initialization: `0x3473`
- USB ISP entry stub: `0x77AA`, which jumps to bootloader address `0xFF00`

The application is ordinary, unobfuscated 8051 machine code and can be
disassembled directly. The compiler runtime clears 128 bytes of internal RAM
and 4096 bytes of XRAM before entering the application.

## GPIO initialization

The startup path calls the GPIO initialization routine at `0x62F1`. It writes
the following SH68F90A port direction and initial-output masks:

| Port | Direction (`PxCR`) | Initial output (`Px`) |
| --- | ---: | ---: |
| P0 | `0x1E` | `0x1E` |
| P1 | `0x3F` | `0x3F` |
| P2 | `0x3F` | `0x3F` |
| P3 | `0x3B` | `0x3F` |
| P4 | `0x00` | `0x00` |
| P5 | `0x07` | `0x07` |
| P6 | `0x3F` | `0x3F` |
| P7 | `0x00` | `0x00` |

On this MCU, a set `PxCR` bit selects output and a clear bit selects input.
The routine enables pull-ups broadly and configures the P1, P2, P3, and P5
high-current drive controls for 25 mA mode.

## Matrix and pin mapping

The PWM initialization routine begins at `0x24A7` and configures all five PWM
groups. The key-processing routine at `0x090C` contains an outer loop with an
exclusive limit of `0x15` (21) and initializes its inner row count to 6. The
keyboard's readable keymap report independently contains exactly 126
four-byte entries. Together these establish a **6-row by 21-column logical
matrix**: `6 * 21 = 126`, with unused positions in the full-size layout.

The timer/PWM interrupt at `0x5DE6` calls the LED-row routine at `0x5258`.
That routine treats the framebuffer as six consecutive groups of 21 bytes and
selects P6.0-P6.5, active low, for groups 0-5. A replacement-firmware test
with the polarity inverted held every LED on, confirming the original
active-low interpretation.

The key scanner at `0x7129` advances one column per interrupt through all 21
columns. It selects a column through the jump table at `0x305A`, samples six
active-low inputs in `0x5CF5`, and stores the resulting six-bit value. Its pin
mapping is:

| Logical index | Column pin |
| ---: | --- |
| 0-1 | P1.4, P1.5 |
| 2-7 | P2.0-P2.5 |
| 8-13 | P3.0-P3.5 |
| 14-17 | P1.3, P1.2, P1.1, P1.0 |
| 18-20 | P5.0-P5.2 |

| Logical index | Switch input | LED row enable |
| ---: | --- | --- |
| 0 | P7.0 | P6.0 |
| 1 | P7.1 | P6.1 |
| 2 | P7.2 | P6.2 |
| 3 | P7.3 | P6.3 |
| 4 | P5.3 | P6.4 |
| 5 | P5.4 | P6.5 |

The 21 columns are shared by switch scanning and PWM LED sinking. The stock
code deselects all columns after each key sample before returning to LED work.
This topology is a six-row extension of the supported E-YOOSO Z11 SMK target:
its first 14 column pins and five of its row inputs match exactly.

Feature report `0x09` is ordered column first, with six four-byte entries per
column. Decoding it provides the complete ISO full-size keymap, including the
navigation block and numpad. The firmware sends standard position-based HID
usages; Linux's Italian keyboard layout converts those usages to the legends
printed on this keyboard. The stock-only Fn entry at row 5, column 9 is mapped
to the replacement firmware's momentary Fn layer.

The lighting-slot report is not identical to the electrical switch positions
for vertically stabilized keys. Hardware testing places main Enter at row 3,
column 13 and keypad Enter at row 4, column 20. The ISO `<` key is at row 4,
column 13.

Stock routine 0x7269 confirms P0.2/P0.3/P0.4 as active-low Num/Caps/Scroll
Lock indicators. Stock enables their output direction and pull-ups (mask
0x1C at 0x6336). The stock-PWM candidate implements this setup and mapping.
P0.1 and P3.6 remain unconfirmed auxiliary candidates and must not be driven
until their roles are confirmed.

## Safety observations

The stock firmware provides an explicit ISP jump at `0x77AA`. The board does
not successfully return to normal firmware after sinowisp's software reboot;
it requires a USB unplug/replug power cycle. That behavior must be preserved
in operational instructions and a replacement image must retain a reliable
path to the stock bootloader.

SMK's SH68F90 `isp_jump()` is instruction-for-instruction equivalent to the
stock entry stub: clear global interrupts, load B with `0xA5`, load A with
`0x5A`, and jump to `0xFF00`. Its HID report ID remains `0x05` on interface 1.
The guarded write scripts operate on the 60 KiB application geometry only;
they never supply the 4 KiB bootloader as write input.

Static analysis found no reset-vector path or confirmed power-on key chord
that forces ISP independently of the application. Therefore the verified
stock image is usable for PC recovery only while the installed application
can initialize USB and execute the ISP jump. Physical programming through J4
remains the recovery method for a failure before USB initialization.
