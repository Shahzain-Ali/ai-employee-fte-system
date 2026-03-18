#!/bin/bash
# Setup Local Vault Sync — Platinum Tier
# Run on Local (WSL) to configure gitwatch and cron pull
# Usage: bash scripts/setup-local-sync.sh

set -euo pipefail

VAULT_PATH="${VAULT_PATH:-$HOME/vault}"

echo "=== FTE Local Sync Setup ==="

# 1. Install inotify-tools
echo "[1/3] Installing inotify-tools..."
sudo apt install -y inotify-tools

# 2. Install gitwatch
echo "[2/3] Installing gitwatch..."
if ! command -v gitwatch &>/dev/null; then
    git clone https://github.com/gitwatch/gitwatch.git /tmp/gitwatch 2>/dev/null || true
    sudo install -b /tmp/gitwatch/gitwatch.sh /usr/local/bin/gitwatch
    echo "gitwatch installed"
else
    echo "gitwatch already installed"
fi

# 3. Configure cron pull
echo "[3/3] Configuring cron pull..."
if ! crontab -l 2>/dev/null | grep -q "git pull.*vault"; then
    (crontab -l 2>/dev/null; echo "*/3 * * * * cd $VAULT_PATH && git pull --rebase origin main >> $HOME/git-pull.log 2>&1") | crontab -
    echo "Cron pull configured (every 3 min)"
else
    echo "Cron pull already configured"
fi

echo ""
echo "=== Setup complete ==="
echo "Start sync: gitwatch -r origin -b main $VAULT_PATH &"
echo "Or use: bash scripts/start-local.sh (starts everything)"
