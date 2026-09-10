#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [[ ${EUID} -ne 0 ]]; then
    exec sudo -- "$0" "$@"
fi

make -s -C "$script_dir"

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
    echo "Could not locate the KM-G6 vendor HID interface." >&2
    exit 1
fi

echo "Testing the standard lighting report on $hidraw_node."
echo "Sending effect 3 (breathing), full brightness, medium speed."
echo "Fn+PgUp restores the keyboard's factory lighting if needed."
read -r -p 'Press Enter to send, or Ctrl+C to cancel... '
"$script_dir/km-g6ctl" "$hidraw_node" effect 3 5 3
echo "Did the lighting change? Tell Codex what you saw."
