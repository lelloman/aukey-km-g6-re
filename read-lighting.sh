#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [[ ${EUID} -ne 0 ]]; then
    exec sudo -- "$0" "$@"
fi

make -s -C "$script_dir" hid-feature

hidraw_node=""
for uevent in /sys/class/hidraw/hidraw*/device/uevent; do
    [[ -r "$uevent" ]] || continue
    if grep -q '^HID_ID=0003:0000258A:0000002A$' "$uevent" \
        && grep -q 'HID_PHYS=.*input1$' "$uevent"; then
        hidraw_node="/dev/$(basename "$(dirname "$(dirname "$uevent")")")"
        break
    fi
done

if [[ -z "$hidraw_node" || ! -c "$hidraw_node" ]]; then
    echo "AUKEY KM-G6 vendor HID interface not found." >&2
    exit 1
fi

exec "$script_dir/hid-feature" "$hidraw_node" 0x0a 41
