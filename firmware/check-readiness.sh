#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
candidate="$repo_root/firmware/build/aukey-km-g6_stock-pwm-candidate.hex"
stock_app="$repo_root/hardware/backups/km-g6-stock-firmware-isp.bin"
stock_full_1="$repo_root/hardware/backups/km-g6-stock-full-1.bin"
stock_full_2="$repo_root/hardware/backups/km-g6-stock-full-2.bin"
sinowisp_bin=${SINOWISP_BIN:-$repo_root/firmware/build/sinowisp/target/release/sinowisp}

check_hash() {
    local expected=$1
    local file=$2
    echo "$expected  $file" | sha256sum --check
}

check_hash 7dd6dada98cc4c5bd846ba496e362f3a418918a1eeae5843aedc9ab907a2065f "$candidate"
(cd "$repo_root/hardware/backups" && sha256sum --check SHA256SUMS)

cmp --silent "$stock_full_1" "$stock_full_2"
cmp --silent <(head -c 61440 "$stock_full_1") "$stock_app"
[[ -x "$sinowisp_bin" ]] || { echo "sinowisp not found at $sinowisp_bin; run firmware/build-sinowisp.sh" >&2; exit 1; }
[[ $(stat --format=%s "$stock_app") == 61440 ]]
[[ $(stat --format=%s "$stock_full_1") == 65536 ]]
bash -n "$repo_root/firmware/flash-experimental.sh"
bash -n "$repo_root/firmware/restore-stock.sh"

echo "Image, sinowisp, independent stock dumps, sizes, and script syntax: OK"
echo "Important: PC-only recovery still depends on replacement firmware reaching USB ISP."
echo "No verified power-on key combination enters the bootloader."
