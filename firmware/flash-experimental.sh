#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
image="$repo_root/firmware/build/aukey-km-g6_default_smk.hex"
expected_image_sha=90291d167332047ab114be5a467f48cdad6f1b6d72ee59a4ae9a76929be0915b
stock="$repo_root/hardware/backups/km-g6-stock-firmware-isp.bin"
expected_stock_sha=d34032c10e8d483ac690079efc626266f2a561917bd15008f3b0402c49653f2a
sinowisp_bin=${SINOWISP_BIN:-/tmp/km-g6-sinowisp/target/release/sinowisp}

if [[ ${1:-} != --yes-i-accept-brick-risk ]]; then
    echo "Refusing to flash without --yes-i-accept-brick-risk" >&2
    exit 2
fi

[[ -x "$sinowisp_bin" ]] || { echo "sinowisp not found at $sinowisp_bin" >&2; exit 1; }
echo "$expected_image_sha  $image" | sha256sum --check --status || { echo "experimental image hash mismatch" >&2; exit 1; }
echo "$expected_stock_sha  $stock" | sha256sum --check --status || { echo "stock recovery image missing or corrupt" >&2; exit 1; }

echo "Writing the experimental 60 KiB application; the 4 KiB bootloader is not part of this image."
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
    --format ihex \
    --force \
    "$image"

echo "Power-cycle the keyboard if it does not enumerate after software reboot."
