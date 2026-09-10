#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
candidate="$repo_root/firmware/build/aukey-km-g6_default_smk.hex"
stock_app="$repo_root/hardware/backups/km-g6-stock-firmware-isp.bin"
stock_full_1="$repo_root/hardware/backups/km-g6-stock-full-1.bin"
stock_full_2="$repo_root/hardware/backups/km-g6-stock-full-2.bin"

check_hash() {
    local expected=$1
    local file=$2
    echo "$expected  $file" | sha256sum --check
}

check_hash c9045ecd9cfe89b82af7ab8de0d65093fbde466ae243ca00c5332584e3cd0a6b "$candidate"
check_hash d34032c10e8d483ac690079efc626266f2a561917bd15008f3b0402c49653f2a "$stock_app"
check_hash cf2dcfe9b6830e254d031eaeefc8c6974d602a10b0a4c80b95f329ead7a258f5 "$stock_full_1"
check_hash cf2dcfe9b6830e254d031eaeefc8c6974d602a10b0a4c80b95f329ead7a258f5 "$stock_full_2"

cmp --silent "$stock_full_1" "$stock_full_2"
[[ $(stat --format=%s "$stock_app") == 61440 ]]
[[ $(stat --format=%s "$stock_full_1") == 65536 ]]
bash -n "$repo_root/firmware/flash-experimental.sh"
bash -n "$repo_root/firmware/restore-stock.sh"

echo "Artifacts, independent stock dumps, sizes, and script syntax: OK"
echo "Important: PC-only recovery still depends on replacement firmware reaching USB ISP."
echo "No verified power-on key combination enters the bootloader."
