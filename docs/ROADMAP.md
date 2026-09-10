# Roadmap to persistent per-key notifications

## Phase 1: identify the hardware

- [x] Identify the main MCU and PCB revision.
- [x] Confirm the flash geometry and bootloader family from verified dumps.
- Complete identification of any separate LED-driver components.
- Search for the exact PCB revision and obtain the relevant datasheets.
- [x] Determine that the BYK901 is compatible with the supported Sino Wealth
  SH68F90A platform.

Exit condition: flash geometry, bootloader family, and likely recovery pins
are known from evidence rather than the USB ID alone.

## Phase 2: establish recovery before experimentation

- Identify ISP/test pads with continuity measurements if photographs are
  insufficient.
- Choose and obtain an external programmer compatible with the confirmed MCU.
- Document wiring and voltage levels.
- [x] Back up and verify the stock firmware using the confirmed geometry.
- Prove that a stock image can be restored before modifying it.

Exit condition: a failed custom build can be recovered without replacing the
keyboard.

## Phase 3: map the board

- [x] Map the 6x21 switch matrix GPIO rows and columns from stock code.
- [x] Map the shared LED columns and six active-low LED row enables.
- Identify polarity, current limits, and PWM strategy.
- Confirm USB D+/D-, clocking, indicators, and Fn-layer handling.

Exit condition: a small test firmware can scan keys and control one selected
LED without electrical abuse.

## Phase 4: replacement firmware

- [x] Add an AUKEY KM-G6 target to SMK and compile it without flashing.
- [x] Decode report `0x09` and add the complete full-size ISO keymap.
- [x] Implement a versioned USB protocol and persistent 126-key intensity framebuffer.
- [x] Add hash-guarded experimental-flash and verified-stock restore scripts.
- [x] Confirm the replacement ISP jump matches the stock `A=5A`, `B=A5`, `LJMP FF00` sequence.
- [ ] Perform the first hardware flash after explicit final acknowledgement of the remaining brick risk.
- Port or adapt an 8051 keyboard firmware base if the MCU is supported.
- Preserve normal keyboard input, NKRO, media keys, and Fn functions.
- Implement a persistent per-key monochrome framebuffer.
- Add global brightness and safe PWM/current limits.
- Define a host protocol with versioning and a read-back capability.
- Add a watchdog/recovery command that always returns to the bootloader.

Because each KM-G6 key has a fixed-color LED, the desired API controls which
keys are lit and their intensity. It cannot change a key's physical color.

## Phase 5: notification software

Provide a small Linux daemon and CLI along these lines:

```text
km-g6-notify set Q 255
km-g6-notify set ESC 80
km-g6-notify group build-success F1 F2 F3
km-g6-notify clear
```

The daemon should arbitrate notifications by priority and expiry rather than
letting applications fight over the LEDs. Suggested layers:

1. Critical alerts (highest priority)
2. Build/server status
3. Messaging indicators
4. Ambient/base layout

Exit condition: multiple notification sources can update independent keys
persistently without flicker, while the keyboard continues typing normally.
