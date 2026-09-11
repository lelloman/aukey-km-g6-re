# AUKEY KM-G6 reverse engineering

Open research, Linux control tools, and experimental replacement firmware for
the AUKEY KM-G6 mechanical keyboard.

The goal is persistent, software-controlled per-key lighting without breaking
normal keyboard input. The stock firmware exposes useful HID controls, but its
per-key report is only a transient effect. This project documents that protocol,
maps the keyboard hardware, and adds a native 126-key framebuffer to an
experimental [SMK](https://github.com/carlossless/smk) firmware target.

> [!CAUTION]
> The replacement firmware compiles, but has not completed safe hardware
> validation. Flashing it can brick the keyboard. Read the
> [firmware notes](firmware/README.md) and establish a physical recovery path
> before writing anything.

## Status

| Area | State |
| --- | --- |
| Stock HID lighting controls | Working |
| Stock key-map discovery | Working |
| Persistent per-key lighting on stock firmware | Not available |
| Matrix and LED GPIO mapping | Recovered from stock code |
| Replacement SMK target | Builds successfully; experimental |
| Host-controlled 6x21 intensity framebuffer | Implemented; hardware validation pending |
| Verified stock backup | Captured and checked locally; intentionally not published |
| Physical recovery | Not yet proven |

The work targets the tested **AUKEY KM-G6 UK B2 V1.1** board, dated
`20180529`, with USB ID `258a:002a` and device revision `10.36`. Its controller
is marked `BYK901` (`NLA25`, `1918`) and belongs to the Sino Wealth SH68F90A
family. The USB ID is shared by other keyboards, so it is not sufficient to
identify compatible hardware.

## What works with stock firmware

On Linux, build the small HID helpers with:

```sh
make
```

Read-only inspection:

```sh
./read-lighting.sh
./probe-reports.sh
```

Global lighting controls are writable and recoverable by unplugging the
keyboard or pressing `Fn+PgUp`:

```sh
./km-g6 brightness 0   # off
./km-g6 brightness 4   # maximum
./km-g6 effect 1       # stock-firmware effect number
```

The `keys`, `hold`, `test-*`, `capture-*`, and calibration commands are
research tools. They can leave the lighting in a confusing state temporarily,
and they do not provide stable per-key lighting on the stock firmware.

## Experimental replacement firmware

The firmware patch is pinned to a known SMK revision and can be built inside a
Debian Trixie container:

```sh
firmware/build-smk.sh
firmware/check-readiness.sh
```

Building and checking are offline operations with respect to the keyboard;
they do not enter ISP mode or write the device.

The replacement firmware implements HID feature report `0x08`, carrying a
versioned 6x21 monochrome framebuffer. Once compatible firmware is installed,
the host utility is designed to use it like this:

```sh
sudo ./km-g6-frame /dev/hidrawN info
sudo ./km-g6-frame /dev/hidrawN set ROW COL INTENSITY
sudo ./km-g6-frame /dev/hidrawN fill INTENSITY
sudo ./km-g6-frame /dev/hidrawN clear
sudo ./km-g6-frame /dev/hidrawN off
```

Each key has a fixed-color LED. Software can control whether a key is lit and
its intensity, but cannot change its physical color.

For passwordless, restricted lighting control, install the root-owned
[lighting helper](docs/LIGHTING-HELPER.md). The mapping GUI uses that helper
instead of running as root.

Visually calibrate the lighting matrix against the physical Italian ISO
layout with:

```sh
./map-lights-gui.py
```

The GUI lights one firmware slot at maximum intensity and records the physical
key pressed, a clicked layout key, or `None lit` in `lighting-map.json`.
Closing an incomplete mapping discards it, so the next launch starts from the
first slot. A completed mapping is retained.

After the normal pass, probe only the 20 matrix slots currently believed to
be unused with `./map-lights-gui.py --unused`. Those observations are saved
separately in `lighting-map-unused.json`.

## Repository guide

| Path | Contents |
| --- | --- |
| [`docs/PROTOCOL.md`](docs/PROTOCOL.md) | Verified stock HID reports and the replacement host protocol |
| [`docs/FIRMWARE.md`](docs/FIRMWARE.md) | Offline analysis of the stock firmware |
| [`docs/RESEARCH.md`](docs/RESEARCH.md) | Controller identification, evidence, and references |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Work completed and the path to persistent notifications |
| [`docs/TEARDOWN.md`](docs/TEARDOWN.md) | Safe disassembly and hardware-inspection checklist |
| [`firmware/`](firmware/) | SMK target patch, reproducible build, and guarded write tooling |
| [`hardware/`](hardware/) | PCB observations and private-backup documentation |
| `*.c`, `*.sh`, `km-g6` | Linux HID utilities and retained protocol experiments |

Stock firmware images, generated builds, raw captures, and compiled binaries
are excluded from the repository. Backup hashes are documented so local copies
can be verified without redistributing the vendor firmware.

## Safety model

Even an apparent firmware “read” on supported Sino Wealth controllers may
modify flash metadata based on the selected geometry. A wrong target or an
unbootable application can make USB recovery impossible.

Before the first experimental flash:

1. Keep verified stock backups on another machine or disk.
2. Identify and test the physical programming connection.
3. Confirm voltage levels, pinout, flash geometry, and the exact board revision.
4. Review the generated image and accept that the keyboard may still become
   unrecoverable.

The write scripts deliberately require explicit acknowledgement flags and
pinned image hashes. Those checks reduce accidental misuse; they do not make
an unverified flash safe.

## Contributing

Hardware photographs, continuity measurements, protocol captures, firmware
review, and testing on precisely identified KM-G6 revisions are welcome. When
reporting results, include the PCB revision, controller marking, USB device
revision, and the exact command or firmware hash used.

Start with the [roadmap](docs/ROADMAP.md) and keep destructive experiments
separate from observations confirmed on stock firmware.
