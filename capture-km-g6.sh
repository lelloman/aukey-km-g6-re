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
    echo "Could not locate the KM-G6 vendor HID interface (258a:002a input1)." >&2
    exit 1
fi

capture_root="$script_dir/captures"
mkdir -p "$capture_root"
run_dir=$(mktemp -d "$capture_root/run-XXXXXX")

capture()
{
    local label=$1
    local report_id payload_len
    for spec in '0x05 5' '0x09 504' '0x0a 41' '0x0b 126' '0x0c 1920'; do
        read -r report_id payload_len <<<"$spec"
        if ! "$script_dir/hid-feature" "$hidraw_node" "$report_id" "$payload_len" \
            >"$run_dir/$label-${report_id#0x}.hex" \
            2>"$run_dir/$label-${report_id#0x}.error"; then
            printf 'Report %s is not readable: ' "$report_id"
            cat "$run_dir/$label-${report_id#0x}.error"
        fi
    done
}

prompt_and_capture()
{
    local label=$1
    local instruction=$2
    echo
    read -r -p "$instruction Then press Enter here... "
    capture "$label"
}

show_changes()
{
    local before=$1
    local after=$2
    local changed=0
    local old_file new_file report

    echo
    echo "Changes: $before -> $after"
    for old_file in "$run_dir/$before-"*.hex; do
        report=${old_file##*-}
        new_file="$run_dir/$after-$report"
        if ! cmp -s "$old_file" "$new_file"; then
            changed=1
            echo "Report ${report%.hex}:"
            diff -u "$old_file" "$new_file" || true
        fi
    done
    if [[ $changed -eq 0 ]]; then
        echo "  No readable feature-report bytes changed."
    fi
}

echo "KM-G6 node: $hidraw_node"
echo "Capture directory: $run_dir"
echo "Do not press any keyboard lighting controls while the initial snapshot runs."
capture baseline

prompt_and_capture mode 'Press Fn+Insert exactly once.'
prompt_and_capture brightness 'Press Fn+Up exactly once.'
prompt_and_capture speed 'Press Fn+Right exactly once.'

show_changes baseline mode
show_changes mode brightness
show_changes brightness speed

if [[ -n ${SUDO_UID:-} && -n ${SUDO_GID:-} ]]; then
    chown -R "$SUDO_UID:$SUDO_GID" "$run_dir"
fi

echo
echo "Done. Paste the complete output back to me."
