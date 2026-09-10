# Verified stock-firmware protocol notes

These findings apply to the tested AUKEY KM-G6 with USB identity
`258a:002a`, device revision `10.36`. The USB ID is shared by other keyboards,
so software must not apply them blindly to every device with the same ID.

## HID interfaces and reports

The vendor interface is Linux `input1`; its `/dev/hidrawN` number changes after
reconnection. The scripts locate it from sysfs rather than hard-coding a node.

Known vendor-defined feature reports:

| Report | Payload | Observed purpose |
| --- | ---: | --- |
| `0x05` | 5 bytes | Likely normal-firmware ISP/reboot channel; GET stalls |
| `0x09` | 504 bytes | Readable 6x21 physical-slot to HID-usage key map (126 four-byte entries) |
| `0x0a` | 41 bytes | Readable/writable global lighting state |
| `0x0b` | 126 bytes | Writable transient per-key lighting mask; GET stalls |
| `0x0c` | 1920 bytes | Unknown; GET stalls |

`HIDIOCGFEATURE` returning `EPIPE`/“Broken pipe” means that report is not
readable through the stock firmware. It does not imply that every SET request
for the same report is unsupported.

## Report `0x0a`: global state

Including the report ID, representative reports are:

```text
0a 01 01 02 04 00 ...   factory mode, brightness 4
0a 02 01 02 04 00 ...   after Fn+Insert changes mode
0a 04 09 02 04 00 ...   custom profile selected with Fn+9
0a 01 01 02 00 00 ...   brightness zero
```

Verified or strongly supported byte meanings:

| Offset | Meaning |
| ---: | --- |
| 0 | Report ID `0x0a` |
| 1 | Lighting mode |
| 2 | Selected profile (`9`/`10` are custom slots) |
| 3 | Animation speed |
| 4 | Brightness, `0..4` |

Fn+Home edit mode did not expose a distinct flag in the header. Trailing bytes
sometimes contained data resembling a scratch copy of the key map.

## Report `0x09`: key map

The payload contains four-byte HID usages indexed by physical lighting slot.
The tested layout maps Q to slot 8. The current tool validates that fact before
performing an experimental write, reducing the risk of acting on a different
keyboard which reuses the same USB ID.

## Report `0x0b`: per-key mask

A one-shot mask flashes the addressed key and is then overwritten by the
stock lighting renderer. Continuous writes at approximately 20 Hz and 200 Hz
make the key visibly flicker or "tremble"; they do not produce persistent
illumination. An all-keys mask similarly flashes and returns dark.

Sending the mask while the keyboard was in its physical Fn+Home edit mode did
not set the custom profile. Consequently, this report appears to be a
transient renderer/event input rather than persistent profile storage.

## What the stock interface can and cannot do

It can:

- Read and change global mode, brightness, and speed.
- Read the physical-slot key map.
- Trigger transient per-key flashes.

It has not provided:

- A stable host-rendered frame buffer.
- A software command that saves a custom per-key profile.
- Persistent per-key control without the onboard Fn editing sequence.

## Replacement-firmware host lighting protocol

This section applies only after installing the experimental SMK replacement
firmware; stock firmware does not implement report `0x08`.

Report `0x08` is an eight-byte HID feature report on interface 1:

```text
08 VERSION COMMAND OFFSET COUNT DATA0 DATA1 DATA2
```

Version 1 commands are:

| Command | Meaning |
| ---: | --- |
| `1` | Write `COUNT` intensities (1-3) at row-major `OFFSET` |
| `2` | Fill all 126 intensities with `DATA0` |
| `3` | Enable the host framebuffer when `DATA0 != 0`; disable it otherwise |

GET_REPORT returns:

```text
08 01 ACTIVE 06 15 7e 03 00
```

This advertises protocol version 1, active state, 6 rows, 21 columns, 126
slots, and a maximum chunk of three intensity bytes. Intensities range from
0 (off) to 255 (maximum). Disabling host mode returns rendering to the onboard
animation; it does not erase the uploaded frame.

The host CLI uses matrix coordinates:

```text
sudo ./km-g6-frame /dev/hidrawN info
sudo ./km-g6-frame /dev/hidrawN set ROW COL INTENSITY
sudo ./km-g6-frame /dev/hidrawN fill INTENSITY
sudo ./km-g6-frame /dev/hidrawN clear
sudo ./km-g6-frame /dev/hidrawN off
```
