#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
smk_revision=2876de0684c1fb60af010ef0fb9426bb8951fb34
work_dir=$(mktemp -d)
trap 'rm -rf -- "$work_dir"' EXIT
host_uid=$(id -u)
host_gid=$(id -g)
# Pin the container and its packages (SDCC 4.5.0, meson 1.7.0) so the image hash reproduces.
docker_image=debian:trixie-slim@sha256:a29215f6a35e51e22adffa17f89e9d2ef06214e64a2bad10d765c46aea49f11f
debian_snapshot=20261010T000000Z

git clone --quiet https://github.com/carlossless/smk.git "$work_dir/smk"
git -C "$work_dir/smk" checkout --quiet "$smk_revision"
git -C "$work_dir/smk" apply "$repo_root/firmware/smk-aukey-km-g6.patch"

python3 "$repo_root/firmware/test-fn-volume.py" "$work_dir/smk"
python3 "$repo_root/firmware/test-debounce.py" "$work_dir/smk"
python3 "$repo_root/firmware/test-lock-indicators.py"

mkdir -p "$repo_root/firmware/build"

docker run --rm \
    -e DEBIAN_FRONTEND=noninteractive \
    -e HOST_UID="$host_uid" \
    -e HOST_GID="$host_gid" \
    -v "$work_dir/smk:/src" \
    -w /src \
    -e DEBIAN_SNAPSHOT="$debian_snapshot" \
    "$docker_image" \
    bash -lc 'rm -f /etc/apt/sources.list.d/debian.sources && echo "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/$DEBIAN_SNAPSHOT trixie main" > /etc/apt/sources.list && apt-get update >/dev/null && apt-get install -y --no-install-recommends meson ninja-build sdcc build-essential python3 >/dev/null && ln -s /usr/bin/true /usr/local/bin/sinowisp && meson setup build && ninja -C build aukey-km-g6_default_smk.hex && chown -R "$HOST_UID:$HOST_GID" /src/build'

cp "$work_dir/smk/build/aukey-km-g6_default_smk.hex" "$repo_root/firmware/build/aukey-km-g6_stock-pwm-candidate.hex"
echo "Built firmware/build/aukey-km-g6_stock-pwm-candidate.hex (compile-only; do not flash yet)."
