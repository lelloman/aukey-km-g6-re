# AUKEY KM-G6 control project

Reverse engineering and, eventually, replacement firmware for persistent
per-key lighting control on the AUKEY KM-G6 (`258a:002a`).

## Current status

The keyboard's normal HID interface can control the global lighting mode,
brightness, and speed. It also accepts a per-key mask, but the stock firmware
renders that mask only as a transient flash. Repeated writes produce visible
flicker rather than stable illumination.

**Persistent software-controlled keys are not available through the protocol
we have found.** Replacement firmware appears practical, but recovery must be
established before entering ISP or writing the controller.

The controller is marked `BYK901` (`NLA25`, `1918`) in an LQFP64 package, which
identifies the Sino Wealth SH68F90A family. The PCB is marked
`KM-G6 UK B2 V1.1`, dated `20180529`. Two full USB-ISP reads have produced
byte-identical 64 KiB stock backups, including a recognized 4 KiB bootloader.
Do not attempt a firmware write until the backup has been copied off-machine
and the proposed image has been reviewed.

## Project map

```text
km-g6-control/
├── README.md                 project overview and safe commands
├── Makefile                  builds the Linux HID research tools
├── km-g6                     experimental command-line wrapper
├── *.c / *.sh                protocol probes retained from experiments
├── captures/                 raw HID captures
├── docs/
│   ├── TEARDOWN.md           opening, cleaning, and photo checklist
│   ├── PROTOCOL.md           verified HID findings
│   ├── RESEARCH.md           controller evidence and references
│   ├── FIRMWARE.md           offline stock-firmware analysis
│   └── ROADMAP.md            route to persistent control
└── hardware/
    └── photos/               place teardown photographs here
```

## What is safe to use now

Build the helpers:

```sh
make
```

Read the current global lighting state without writing:

```sh
./read-lighting.sh
```

Read the known feature reports without writing:

```sh
./probe-reports.sh
```

Global lighting commands are writable but recoverable with `Fn+PgUp` or by
unplugging the keyboard:

```sh
./km-g6 brightness 0   # off
./km-g6 brightness 4   # maximum
./km-g6 effect 1       # raw stock-firmware mode number
```

The `keys`, `hold`, `test-*`, `capture-*`, and calibration programs are
research tools. They do **not** provide persistent per-key lighting and may
temporarily leave the stock lighting in a confusing state.

## Next session

When there is time to remove and clean the keycaps, follow
[`docs/TEARDOWN.md`](docs/TEARDOWN.md). We need clear photographs of the full
PCB, controller marking, board revision, LED-driver components, and USB area.
No desoldering is required for this inspection.

After identifying the hardware, continue with [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Hard safety boundary

There are deliberately no firmware-dumping or flashing scripts in this
project yet. On compatible Sino Wealth controllers, even a nominal firmware
"read" can modify the flash enable/jump bytes using an assumed firmware size.
A wrong assumption can prevent the keyboard from booting. We first need:

1. A confirmed MCU marking and PCB revision.
2. A verified flash geometry and ISP method.
3. A stock-firmware backup strategy.
4. A physical recovery programmer or a consciously accepted no-recovery risk.
