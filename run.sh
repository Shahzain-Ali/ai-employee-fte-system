#!/bin/bash
# Personal AI Employee — Development run script
# Usage: ./run.sh [setup|run|test|status|stop]

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=".venv/bin/python"

command="${1:-help}"

case "$command" in
  setup)
    echo "Setting up AI Employee vault..."
    "$PYTHON" -m src.main setup
    ;;
  run)
    echo "Starting AI Employee system..."
    "$PYTHON" -m src.main run
    ;;
  test)
    echo "Running tests..."
    "$PYTHON" -m pytest tests/ -v
    ;;
  status)
    pm2 status fte-system 2>/dev/null || echo "PM2 not running"
    ;;
  stop)
    pm2 stop fte-system 2>/dev/null || echo "Not running under PM2"
    ;;
  pm2-start)
    echo "Starting with PM2..."
    mkdir -p logs
    pm2 start ecosystem.config.js
    pm2 save
    ;;
  pm2-stop)
    pm2 stop ecosystem.config.js
    ;;
  pm2-logs)
    pm2 logs fte-system
    ;;
  help|*)
    echo "Personal AI Employee — Bronze Tier"
    echo ""
    echo "Commands:"
    echo "  ./run.sh setup      Initialize vault structure"
    echo "  ./run.sh run        Start watcher + orchestrator (foreground)"
    echo "  ./run.sh test       Run all tests"
    echo "  ./run.sh pm2-start  Start with PM2 (background)"
    echo "  ./run.sh pm2-stop   Stop PM2 process"
    echo "  ./run.sh pm2-logs   View PM2 logs"
    echo "  ./run.sh status     Check PM2 status"
    ;;
esac
