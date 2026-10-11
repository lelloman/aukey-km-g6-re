#!/usr/bin/env bash
set -euo pipefail

# Read the stock firmware twice over USB ISP, check the reads match, and
# extract the 60 KiB application region that restore-stock.sh writes back.
# Run with sudo while the keyboard still runs its stock firmware.
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
backups="$repo_root/hardware/backups"
full_1="$backups/km-g6-stock-full-1.bin"
full_2="$backups/km-g6-stock-full-2.bin"
stock="$backups/km-g6-stock-firmware-isp.bin"
reference_full_sha=cf2dcfe9b6830e254d031eaeefc8c6974d602a10b0a4c80b95f329ead7a258f5
sinowisp_bin=${SINOWISP_BIN:-$repo_root/firmware/build/sinowisp/target/release/sinowisp}

[[ -x "$sinowisp_bin" ]] || { echo "sinowisp not found at $sinowisp_bin; run firmware/build-sinowisp.sh (without sudo)" >&2; exit 1; }
for f in "$full_1" "$full_2" "$stock"; do
    [[ ! -e "$f" ]] || { echo "Refusing to overwrite existing backup $f" >&2; exit 1; }
done
if lsusb -d 258a:002a | grep -q SMK; then
    echo "The keyboard is running SMK, not stock firmware; a backup now would not be a stock backup." >&2
    exit 1
fi

read_full() {
    "$sinowisp_bin" read \
        --platform sh68f90 \
        --vendor_id 0x258a \
        --product_id 0x002a \
        --firmware_size 61440 \
        --bootloader_size 4096 \
        --page_size 2048 \
        --isp_iface_num 1 \
        --isp_report_id 5 \
        --section full \
        --format bin \
        "$1"
}

read_full "$full_1"
echo "First read done. Unplug and replug the keyboard, then press Enter."
read -r
read_full "$full_2"

cmp --silent "$full_1" "$full_2" || { echo "The two reads differ; do not flash. Keep both files and retry." >&2; exit 1; }
[[ $(stat --format=%s "$full_1") == 65536 ]] || { echo "Unexpected full read size" >&2; exit 1; }

head -c 61440 "$full_1" > "$stock"
(cd "$backups" && sha256sum "$(basename "$full_1")" "$(basename "$stock")" > SHA256SUMS)
if [[ -n ${SUDO_USER:-} ]]; then
    chown "$SUDO_USER:" "$full_1" "$full_2" "$stock" "$backups/SHA256SUMS"
fi

if [[ $(sha256sum < "$full_1" | cut -d' ' -f1) == "$reference_full_sha" ]]; then
    echo "Backup matches the reference KM-G6 stock dump."
else
    echo "Backup is consistent but differs from the reference KM-G6 stock dump;"
    echo "your keyboard may run a different stock revision. Flash with extra care."
fi
echo "Backups written to hardware/backups/. Copy them to another disk before flashing."
echo "Unplug and replug the keyboard to return it to normal operation."
