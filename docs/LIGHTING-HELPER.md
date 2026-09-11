# Restricted lighting helper

`km-g6-lighting` is the intended sudoers entry point. Unlike the development
tools, it takes no device path, file path, raw report, firmware, or executable
argument. It executes no other programs and reads no configuration or
environment-selected paths.

It discovers `/dev/hidraw*`, rejects symlinks, checks USB VID/PID `258a:002a`
and the vendor interface (`/input1`), and verifies replacement lighting
protocol 1, report 8, dimensions 6×21 and chunk size 3 before writing. It
uses the same validated open descriptor and refuses multiple matching devices.
Only the eight-byte lighting protocol is writable—not stock configuration
or the firmware-flashing protocol. Hardware identity is not cryptographic;
this is a limited control interface, not protection against malicious USB hardware.

## One-time installation

Build as your normal user. Install the binary into a root-owned directory;
never whitelist a binary or script in this user-writable checkout.

```sh
make km-g6-lighting
sudo install -o root -g root -m 0755 km-g6-lighting /usr/local/sbin/km-g6-lighting
sudo visudo -cf packaging/km-g6-lighting.sudoers
sudo install -o root -g root -m 0440 packaging/km-g6-lighting.sudoers /etc/sudoers.d/km-g6-lighting
sudo visudo -c
```

The rule grants `YOUR_USERNAME` passwordless lighting control only. Change that
username before installing if needed. The target directories must remain
root-owned and not writable by ordinary users. Do not grant sudo access to
`bash`, `python`, `make`, `hid-feature`, or the workspace tools for this task.
On updates, rebuild as your user and repeat only the binary installation.
No system installation is performed by `make`.

## Commands

```sh
sudo -n /usr/local/sbin/km-g6-lighting info
sudo -n /usr/local/sbin/km-g6-lighting set 4 5 255
sudo -n /usr/local/sbin/km-g6-lighting fill 128
sudo -n /usr/local/sbin/km-g6-lighting clear
```

Rows are 0–5, columns 0–20, intensity 0–255. `on` enables the host frame;
`off` returns to the onboard lighting effect, **not blackout**. Use `clear`
for blackout. Lock-status LEDs remain controlled by the OS.

The mapping GUI uses this installed helper and does not run as root.

To revoke passwordless access, remove only `/etc/sudoers.d/km-g6-lighting`
and check the remaining policy with `sudo visudo -c`.
