#!/bin/bash
# Start Local Agent — Platinum Tier
# Auto-starts on laptop boot via Windows Task Scheduler + VBS launcher
# Usage: bash scripts/start-local.sh

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
VAULT_PATH="${VAULT_PATH:-$HOME/vault}"
LOG="$HOME/fte-local-start.log"

echo "=== FTE Local Agent Start — $(date -u) ===" | tee -a "$LOG"

# Load environment
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Pull latest vault
echo "Pulling latest vault..." | tee -a "$LOG"
if [ -d "$VAULT_PATH/.git" ]; then
    cd "$VAULT_PATH" && git pull --rebase origin main 2>&1 | tee -a "$LOG" || true
else
    echo "Vault not found at $VAULT_PATH — clone it first" | tee -a "$LOG"
fi

# Start Local Orchestrator in background
echo "Starting Local Orchestrator..." | tee -a "$LOG"
cd "$PROJECT_DIR"
nohup uv run python -m src.orchestrator.local_orchestrator >> "$HOME/fte-local-orchestrator.log" 2>&1 &
echo "Local Orchestrator PID: $!" | tee -a "$LOG"

# Start gitwatch for vault (if available)
if command -v gitwatch &>/dev/null && [ -d "$VAULT_PATH/.git" ]; then
    nohup gitwatch -r origin -b main "$VAULT_PATH" >> "$HOME/fte-gitwatch.log" 2>&1 &
    echo "gitwatch started for vault PID: $!" | tee -a "$LOG"
fi

# Setup cron pull if not already configured
if ! crontab -l 2>/dev/null | grep -q "git pull.*vault"; then
    (crontab -l 2>/dev/null; echo "*/3 * * * * cd $VAULT_PATH && git pull --rebase origin main >> $HOME/git-pull.log 2>&1") | crontab -
    echo "Cron git pull configured (every 3 min)" | tee -a "$LOG"
fi

echo "=== Local Agent started — $(date -u) ===" | tee -a "$LOG"
