#!/bin/bash
# Start Cloud Agent — Platinum Tier
# Starts all Cloud processes: orchestrator, gitwatch, cron pull
# Usage: bash scripts/start-cloud.sh

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/fte-project}"
VAULT_PATH="${VAULT_PATH:-/home/ubuntu/vault}"
LOG="/var/log/fte/cloud-start.log"

echo "=== FTE Cloud Agent Start — $(date -u) ===" | tee -a "$LOG"

# Load environment
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
    echo "Loaded .env" | tee -a "$LOG"
fi

# Pull latest vault changes
echo "Pulling latest vault..." | tee -a "$LOG"
cd "$VAULT_PATH" && git pull --rebase origin main 2>&1 | tee -a "$LOG" || true

# Start PM2 ecosystem
echo "Starting PM2 ecosystem..." | tee -a "$LOG"
cd "$PROJECT_DIR"
pm2 start config/ecosystem.config.js 2>&1 | tee -a "$LOG"
pm2 save 2>&1 | tee -a "$LOG"

# Setup cron pull (every 3 minutes) if not already set
if ! crontab -l 2>/dev/null | grep -q "git pull.*vault"; then
    (crontab -l 2>/dev/null; echo "*/3 * * * * cd $VAULT_PATH && git pull --rebase origin main >> /var/log/fte/git-pull.log 2>&1") | crontab -
    echo "Cron git pull configured (every 3 min)" | tee -a "$LOG"
else
    echo "Cron git pull already configured" | tee -a "$LOG"
fi

echo "=== Cloud Agent started — $(date -u) ===" | tee -a "$LOG"
echo ""
pm2 status
