#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
results=$(mktemp /tmp/km-g6-effects-XXXXXX.txt)

echo "This will test KM-G6 effect values 1 through 20."
echo "For each value, watch the keyboard briefly and type what it does."
echo "Type 'stop' as the description to finish early."
echo

for mode in $(seq 1 20); do
    read -r -p "Press Enter to send effect $mode... "
    "$script_dir/km-g6" effect "$mode" 5 3
    read -r -p "Effect $mode description: " description
    printf '%2d: %s\n' "$mode" "$description" | tee -a "$results"
    [[ $description != stop ]] || break
done

echo
echo "Results:"
cat "$results"
rm -f "$results"
echo "Paste that table back to Codex."
