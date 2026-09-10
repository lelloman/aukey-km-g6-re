#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [[ ${EUID} -ne 0 ]]; then
    exec sudo -- "$0" "$@"
fi

echo "During the countdown, press Fn+Home once and release both keys."
for seconds in 5 4 3 2 1; do
    echo "$seconds..."
    sleep 1
done

echo "Reading edit-mode state now:"
exec "$script_dir/read-lighting.sh"
