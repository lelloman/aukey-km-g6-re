#!/usr/bin/env bash
set -euo pipefail

# Build the pinned sinowisp flasher into firmware/build/sinowisp; run without sudo.
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
sinowisp_revision=9caf1c9e4f332388dc4748f3f449d604c66ca43e
src="$repo_root/firmware/build/sinowisp"

if [[ ! -d "$src/.git" ]]; then
    mkdir -p "$repo_root/firmware/build"
    git clone --quiet https://github.com/carlossless/sinowisp.git "$src"
fi
git -C "$src" fetch --quiet origin "$sinowisp_revision" 2>/dev/null || true
git -C "$src" checkout --quiet --detach "$sinowisp_revision"

cargo build --release --locked --manifest-path "$src/Cargo.toml"

echo "Built firmware/build/sinowisp/target/release/sinowisp ($sinowisp_revision)"
