#!/bin/bash
# Health Monitor — cron wrapper for health_monitor.py
# Runs every 5 minutes via PM2 or cron:
#   */5 * * * * /home/ubuntu/fte-project/scripts/health-monitor.sh >> /var/log/fte-health/cron.log 2>&1

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/fte-project}"
VAULT_PATH="${VAULT_PATH:-/home/ubuntu/vault}"
LOG_DIR="/var/log/fte-health"

mkdir -p "$LOG_DIR"

export VAULT_PATH

cd "$PROJECT_DIR"
uv run python -m src.health.health_monitor 2>&1 | tee -a "$LOG_DIR/cron.log"
