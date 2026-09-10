#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
stock="$repo_root/hardware/backups/km-g6-stock-firmware-isp.bin"
expected_stock_sha=d34032c10e8d483ac690079efc626266f2a561917bd15008f3b0402c49653f2a
sinowisp_bin=${SINOWISP_BIN:-/tmp/km-g6-sinowisp/target/release/sinowisp}

if [[ ${1:-} != --restore-verified-stock ]]; then
    echo "Refusing to write without --restore-verified-stock" >&2
    exit 2
fi

[[ -x "$sinowisp_bin" ]] || { echo "sinowisp not found at $sinowisp_bin" >&2; exit 1; }
echo "$expected_stock_sha  $stock" | sha256sum --check --status || { echo "stock recovery image missing or corrupt" >&2; exit 1; }
[[ $(stat --format=%s "$stock") == 61440 ]] || { echo "stock recovery image is not exactly 61440 bytes" >&2; exit 1; }

echo "Restoring the verified stock 60 KiB application; the bootloader is not being overwritten."
"$sinowisp_bin" write \
    --platform sh68f90 \
    --vendor_id 0x258a \
    --product_id 0x002a \
    --firmware_size 61440 \
    --bootloader_size 4096 \
    --page_size 2048 \
    --isp_iface_num 1 \
    --isp_report_id 5 \
    --reboot true \
    --format bin \
    "$stock"

echo "Power-cycle the keyboard if it does not enumerate after software reboot."
