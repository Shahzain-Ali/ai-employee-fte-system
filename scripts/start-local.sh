#!/bin/bash
# Start Local Agent — Platinum Tier
# Auto-starts on laptop boot via Windows Task Scheduler + VBS launcher
# Usage: bash scripts/start-local.sh

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/e/hackathon-0/full-time-equivalent-project}"
LOG="$HOME/fte-local-start.log"

echo "=== FTE Local Agent Start — $(date -u) ===" | tee -a "$LOG"

# Load environment
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Pull latest from GitHub
echo "Pulling latest code..." | tee -a "$LOG"
cd "$PROJECT_DIR" && git pull --rebase origin main 2>&1 | tee -a "$LOG" || true

# Start Local Orchestrator in background
echo "Starting Local Orchestrator..." | tee -a "$LOG"
cd "$PROJECT_DIR"
nohup uv run python -m src.main run >> "$HOME/fte-local-orchestrator.log" 2>&1 &
echo "Local Orchestrator PID: $!" | tee -a "$LOG"

# Setup cron pull if not already configured
if ! crontab -l 2>/dev/null | grep -q "git pull.*fte-project"; then
    (crontab -l 2>/dev/null; echo "*/3 * * * * cd $PROJECT_DIR && git pull --rebase origin main >> $HOME/git-pull.log 2>&1") | crontab -
    echo "Cron git pull configured (every 3 min)" | tee -a "$LOG"
fi

echo "=== Local Agent started — $(date -u) ===" | tee -a "$LOG"
