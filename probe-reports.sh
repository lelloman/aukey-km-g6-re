#!/usr/bin/env bash
set -u

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [[ ${EUID} -ne 0 ]]; then
    exec sudo -- "$0" "$@"
fi

make -s -C "$script_dir" hid-feature || exit 1

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

echo "Probing $hidraw_node without writing to it..."
for spec in '0x0a 41' '0x09 504' '0x0b 126' '0x0c 1920' '0x05 5'; do
    read -r report_id payload_len <<<"$spec"
    echo
    echo "--- report $report_id ($payload_len payload bytes) ---"
    "$script_dir/hid-feature" "$hidraw_node" "$report_id" "$payload_len" || true
done
