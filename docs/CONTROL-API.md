# Exposing keyboard controls to other programs

## Available now: local command interface

Use the installed `/usr/local/sbin/km-g6-lighting` executable as the control
boundary. Applications run as the logged-in user and invoke only that helper
through passwordless sudo. See [installation and sudoers setup](LIGHTING-HELPER.md).
The template's `YOUR_USERNAME` must be replaced with the actual local account
before installation; sudoers does not expand `$USER`.

This requires the compatible replacement firmware. It controls lighting,
not typing, key remapping, OS lock indicators, or firmware updates.
There is currently **no HTTP server, socket API, or alarm-message endpoint**.

| Arguments after the helper path | Behavior |
| --- | --- |
| `info` | Read protocol, active state, dimensions and chunk size |
| `set ROW COL INTENSITY` | Change one slot, preserve others, activate host lighting |
| `fill INTENSITY` | Set every slot and activate host lighting |
| `clear` | Set every slot to zero and activate host lighting |
| `on` | Activate the existing host frame |
| `off` | Return to the firmware's onboard effect; **not blackout** |

Rows are 0–5, columns 0–20, intensity 0–255. Use plain decimal arguments.
There are 126 electrical slots, including unused positions. Every physical
key has a fixed LED colour; RGB colour selection is not supported.

Verified positions include ESC `(0,1)`, F1–F12 `(0,2)` through `(0,13)`,
A `(3,1)`, B `(4,5)`, and R `(2,4)`. Use the observed results in
[`lighting-map.json`](../lighting-map.json) and
[`lighting-map-unused.json`](../lighting-map-unused.json) for other keys;
the original `expected` label is not always the physical observation.

```sh
sudo -n -- /usr/local/sbin/km-g6-lighting info
sudo -n -- /usr/local/sbin/km-g6-lighting set 0 1 255
sudo -n -- /usr/local/sbin/km-g6-lighting clear
```

Successful commands exit 0. The helper exits 2 for invalid arguments and 1
for device/protocol or I/O failures. Sudo itself can also fail, so treat any
nonzero status as failure and surface stderr. `info` prints space-separated
`key=value` fields; setters normally print nothing. Example:

```text
protocol=1 active=1 rows=6 cols=21 keys=126 chunk=3
```

Use an argument list, not a shell string, when calling from an application:

```python
import subprocess

def lighting(*args):
    return subprocess.run(
        ["sudo", "-n", "--", "/usr/local/sbin/km-g6-lighting", *map(str, args)],
        check=True, capture_output=True, text=True, timeout=5,
    ).stdout

lighting("set", 0, 1, 255)
```

`sudo -n` fails instead of waiting for a password. Do not whitelist a shell,
Python interpreter, workspace binary, or general HID utility. The installed
helper and its parent directory must remain root-owned and not user-writable.
It validates the device/interface and protocol, accepts no supplied device
path, and never executes another program.

## Ownership: avoid two writers

The helper does not arbitrate between callers. Before direct writes, stop
the base service and any manual program or mapping GUI:

```sh
systemctl --user stop km-g6-base
# Send lighting commands here.
sudo -n -- /usr/local/sbin/km-g6-lighting clear
systemctl --user start km-g6-base
```

For an automated integration, remember whether the service was running and
restore that state in a `finally` block, including after errors or Ctrl-C.
Do not start a service that the user had deliberately left stopped.
The base program's lock prevents duplicate program instances, but raw helper
commands and the mapping GUI do not acquire that lock.

For the already-supported disk alarm demonstration, use:

```sh
./keyboard_program.py preview-disk-alarm --seconds 10
```

That command handles the service pause and restoration. It consumes no disk
space. It is a preview, not a persistent alarm API.

Updates are not atomic across multiple helper calls. Send commands serially,
update only changed keys, and avoid clearing the frame on every animation
step. The helper includes USB pacing and performs discovery on each call;
this interface is suitable for indicators, not high-frame-rate graphics.

## Future extension: one local controller, multiple clients

If notifications need to coexist with the base program, add a Unix-domain
socket to the unprivileged controller rather than launching competing writers.
This is a proposed design, not implemented functionality:

- Bind under the user's runtime directory with owner-only permissions.
- Accept bounded, validated messages for operations such as set/clear alarm,
  temporary preview, program selection, and status.
- Keep all rendering in the controller; alarm overlays temporarily override
  the base frame, and clearing them restores current metrics.
- Return request IDs and explicit success/error responses. Limit message
  sizes, rates and preview duration; never accept shell commands or paths.
- Define disconnect, expiry, acknowledgment and restart behavior before
  exposing persistent alarms.

Keep the privileged helper unchanged underneath that controller. Do not expose
raw sudo or HID access over HTTP. A remote interface would need a separate,
authenticated gateway and an explicit authorization design.
