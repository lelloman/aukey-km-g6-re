#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -eq 0 ]]; then
    echo "Run this as your normal user, not with sudo." >&2
    exit 2
fi
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [[ ! -x /usr/local/sbin/km-g6-lighting ]]; then
    echo "Install the restricted helper first: docs/LIGHTING-HELPER.md" >&2
    exit 1
fi
# Verify the current user's passwordless policy and keyboard before enabling.
sudo -n -- /usr/local/sbin/km-g6-lighting info
systemd-analyze --user verify "$repo_root/packaging/km-g6-base.service"
install -d -m 0755 "$HOME/.local/share/km-g6-control" "$HOME/.config/systemd/user"
install -m 0644 "$repo_root/keyboard_program.py" "$HOME/.local/share/km-g6-control/keyboard_program.py"
install -m 0644 "$repo_root/packaging/km-g6-base.service" "$HOME/.config/systemd/user/km-g6-base.service"
systemctl --user daemon-reload
systemctl --user enable km-g6-base.service
systemctl --user restart km-g6-base.service
systemctl --user --no-pager status km-g6-base.service
