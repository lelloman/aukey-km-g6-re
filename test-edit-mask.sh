#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [[ ${EUID} -ne 0 ]]; then
    exec sudo -- "$0" "$@"
fi

make -s -C "$script_dir" km-g6-keys

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

echo "During the countdown, press Fn+Home once to enter editing mode."
for seconds in 5 4 3 2 1; do
    echo "$seconds..."
    sleep 1
done

echo "Sending the Q-only mask now."
"$script_dir/km-g6-keys" "$hidraw_node" Q
echo "Observe the keyboard, then press Fn+End to leave editing mode."
