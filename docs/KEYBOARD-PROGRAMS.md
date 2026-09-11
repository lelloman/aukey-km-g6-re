# Keyboard programs

Run programs as your normal user, after the one-time
[restricted lighting helper installation](LIGHTING-HELPER.md).
No new firmware or helper rebuild is required for the base program.

```sh
./keyboard_program.py base
```

The base program uses cumulative bars at maximum brightness:

| CPU utilization | CPU keys | Available disk space | Disk keys |
| --- | --- | --- | --- |
| >20% | F1 | ≤50 GB | F5 |
| >40% | F1–F2 | ≤40 GB | F5–F6 |
| >60% | F1–F3 | ≤30 GB | F5–F7 |
| >80% | F1–F4 | ≤20 GB | F5–F8 |

Below 10 GB, F5–F8 flash together, alternating on/off every half second;
CPU indicators remain steady. At exactly 10 GB the disk warning stays solid.

RAM warnings use F9–F12, cumulatively above 60%, 75%, 85%, and 95% used.
Above 98%, all four flash together every half second (at exactly 98% they
stay solid). RAM usage is `(MemTotal - MemAvailable) / MemTotal` from
`/proc/meminfo`, so reclaimable cache is treated as available. This is a
memory-capacity warning, not Linux PSI stall measurement. CPU and disk
indicators are unaffected by RAM flashing; simultaneous critical disk and
RAM warnings flash their respective groups together.

At exactly a threshold the next key stays off: 40% CPU lights only F1.
CPU means aggregate utilization over the sampling interval, not the Linux
load average. Idle and I/O-wait time are excluded; guest time is not counted
twice. Disk means space available to ordinary users, excluding reserved
blocks, on the filesystem containing `--disk-path` (default `/`). GB means
1,000,000,000 bytes, not GiB. Less free space lights more warning keys.

CPU and RAM are sampled once per second. Disk space is checked at startup, then every
20 seconds (`--disk-interval 20`); its cached value drives warning flashing
between checks. Startup clears the backlight; other keys stay
dark. Updates touch only changed indicator keys, without clearing the whole
keyboard each time. OS lock-status LEDs remain independent. Ctrl-C or SIGTERM
stops the program and attempts to clear the backlight; unplugging the keyboard
or forcibly killing the process can prevent cleanup.

```sh
# Preview metrics without sudo or a keyboard:
./keyboard_program.py base --dry-run --once

# Show the actual disk warning for ten seconds without filling the disk:
./keyboard_program.py preview-disk-alarm

# Monitor the root filesystem and use dimmer indicators:
./keyboard_program.py base --disk-path / --brightness 128 --interval 2

# Customize F5/F6/F7/F8 warning levels and the critical flashing threshold:
./keyboard_program.py base --disk-levels 100 80 60 40 --disk-flash-below 20

# Run logic tests without hardware:
python3 -m unittest test_keyboard_program.py
```

Only one instance per user can control the keyboard at a time. Stop it before
running the mapping GUI or other lighting tools: those independent tools do
not yet share its lock. Permission/device errors stop the program with an
explanation.

Warning levels must be strictly descending, nonnegative values. The flashing
threshold must not exceed the F8 threshold. Changing the sampling interval
does not change the half-second flashing cadence.

`preview-disk-alarm` pauses the active base service, flashes F5–F8, clears
the preview, then restarts the service. It also attempts restoration after
Ctrl-C or an error. Stop a manually running base program before previewing.
Use `--seconds 5` to change the preview duration (maximum 30 seconds).

## Run automatically with systemd

Stop any manually running base program first (Ctrl-C), then run as your
normal user, **not with sudo**:

```sh
./install-user-service.sh
```

This installs a copy of the program under `~/.local/share/km-g6-control`
and a user unit under `~/.config/systemd/user`, then enables and starts it.
It checks passwordless helper access before installation. The program stays
unprivileged; only the restricted lighting helper uses sudo. Rerun the
installer after code updates to refresh the installed copy and restart it.

The service starts at login, retries failures after ten seconds, and logs
startup/errors to the journal without logging every CPU sample. A manual
service stop does not trigger a restart and attempts to clear the lights.
The disk-check timer also checks keyboard connectivity (every 20 seconds by
default). A missing keyboard causes a failure/retry; a detected return to the
onboard effect reinitializes the host lighting frame.

```sh
systemctl --user status km-g6-base
journalctl --user -u km-g6-base -n 50 --no-pager
systemctl --user stop km-g6-base    # Before using the mapping GUI
systemctl --user start km-g6-base
systemctl --user disable --now km-g6-base  # Disable automatic startup
```

To change service thresholds, run `systemctl --user edit km-g6-base` and set:

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python3 %h/.local/share/km-g6-control/keyboard_program.py base --quiet --disk-levels 50 40 30 20 --disk-flash-below 10 --disk-interval 20
```

Then run `systemctl --user restart km-g6-base`.

Starting at boot before login, and remaining active after logout, additionally
requires `loginctl enable-linger "$USER"`. That affects the whole user service
manager and is deliberately not enabled by the installer.
