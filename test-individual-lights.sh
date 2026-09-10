#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
delay=${1:-0.35}

if ! [[ $delay =~ ^([0-9]+([.][0-9]*)?|[.][0-9]+)$ ]]; then
    echo "usage: $0 [seconds-per-key]" >&2
    exit 2
fi

if [[ ${EUID} -ne 0 ]]; then
    exec sudo -- "$0" "$@"
fi

make -s -C "$script_dir" km-g6-frame

hidraw_node=""
for uevent in /sys/class/hidraw/hidraw*/device/uevent; do
    [[ -r $uevent ]] || continue
    if grep -q '^HID_ID=0003:0000258A:0000002A$' "$uevent" \
        && grep -q 'HID_PHYS=.*input1$' "$uevent"; then
        hidraw_node="/dev/$(basename "$(dirname "$(dirname "$uevent")")")"
        break
    fi
done

if [[ -z $hidraw_node || ! -c $hidraw_node ]]; then
    echo "AUKEY KM-G6 vendor HID interface not found." >&2
    exit 1
fi

"$script_dir/km-g6-frame" "$hidraw_node" info

rows=(
    '.,ESC,F1,F2,F3,F4,F5,F6,F7,F8,F9,F10,F11,F12,PRTSC,SCROLL,PAUSE,.,.,.,.'
    'GRAVE,1,2,3,4,5,6,7,8,9,0,MINUS,EQUAL,BACKSPACE,INSERT,HOME,PAGEUP,NUMLOCK,KP_SLASH,KP_STAR,KP_MINUS'
    'TAB,Q,W,E,R,T,Y,U,I,O,P,LBRACKET,RBRACKET,ENTER,DELETE,END,PAGEDOWN,KP_7,KP_8,KP_9,KP_PLUS'
    'CAPSLOCK,A,S,D,F,G,H,J,K,L,SEMICOLON,APOSTROPHE,ISO_HASH,ISO_BACKSLASH,.,.,.,KP_4,KP_5,KP_6,.'
    'LSHIFT,Z,X,C,V,B,N,M,COMMA,DOT,SLASH,INTL_BACKSLASH,RSHIFT,MENU,.,UP,.,KP_1,KP_2,KP_3,.'
    'LCTRL,LGUI,LALT,.,.,SPACE,.,.,RALT,FN,MENU,.,RCTRL,.,LEFT,DOWN,RIGHT,KP_0,.,KP_DOT,.'
)

cleanup()
{
    "$script_dir/km-g6-frame" "$hidraw_node" clear >/dev/null 2>&1 || true
    "$script_dir/km-g6-frame" "$hidraw_node" off >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "Lighting each populated key alone for ${delay}s; press Ctrl-C to stop."
for row in "${!rows[@]}"; do
    IFS=, read -r -a names <<< "${rows[$row]}"
    for col in "${!names[@]}"; do
        [[ ${names[$col]} == . ]] && continue
        "$script_dir/km-g6-frame" "$hidraw_node" clear
        "$script_dir/km-g6-frame" "$hidraw_node" set "$row" "$col" 255
        printf '%-16s row=%d col=%d\n' "${names[$col]}" "$row" "$col"
        sleep "$delay"
    done
done

echo "Sweep complete; restoring the firmware's normal lighting effect."
