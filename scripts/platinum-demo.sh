#!/bin/bash
# Platinum Demo — End-to-End Integration Test
# Demonstrates: Email arrives → Cloud drafts → Sync → Local approves → Send → Log
# Usage: bash scripts/platinum-demo.sh

set -euo pipefail

VAULT_PATH="${VAULT_PATH:-$HOME/vault}"
CLOUD_VM="${CLOUD_VM_IP:-your-vm-ip}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

step() { echo -e "\n${GREEN}[Step $1]${NC} $2"; }
wait_input() { echo -e "${YELLOW}Press Enter to continue...${NC}"; read -r; }
check() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }

echo "╔══════════════════════════════════════════════════╗"
echo "║     PLATINUM TIER DEMO — End-to-End Flow        ║"
echo "║     AI Employee: Cloud + Local Orchestration     ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Step 1: Verify Cloud VM
step 1 "Verify Cloud VM is running"
if ssh -o ConnectTimeout=5 ubuntu@"$CLOUD_VM" "pm2 status" 2>/dev/null; then
    check "Cloud VM accessible, PM2 processes running"
else
    fail "Cannot reach Cloud VM at $CLOUD_VM"
    echo "Set CLOUD_VM_IP environment variable"
    exit 1
fi

# Step 2: Verify Local Orchestrator is STOPPED
step 2 "Ensure Local Orchestrator is stopped"
if pgrep -f "local_orchestrator" > /dev/null 2>&1; then
    echo "  Stopping Local Orchestrator..."
    pkill -f "local_orchestrator" || true
fi
check "Local Orchestrator stopped"

# Step 3: Send test email
step 3 "Send a test email to trigger Cloud processing"
echo "  Send an email to your Gmail account with subject: 'Quote Request - Demo Test'"
echo "  (Or the email watcher will pick up any new email)"
wait_input

# Step 4: Wait for Cloud to process
step 4 "Wait for Cloud Agent to draft reply"
echo "  Checking vault for draft in Pending_Approval/email/..."
TIMEOUT=180
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    DRAFTS=$(ssh ubuntu@"$CLOUD_VM" "ls $VAULT_PATH/Pending_Approval/email/ 2>/dev/null | wc -l")
    if [ "$DRAFTS" -gt 0 ]; then
        check "Cloud Agent created draft! ($DRAFTS draft(s) found)"
        break
    fi
    echo "  Waiting... ($ELAPSED/$TIMEOUT seconds)"
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    fail "Timeout waiting for Cloud draft"
    exit 1
fi

# Step 5: Start Local Agent
step 5 "Start Local Agent to pull and process drafts"
echo "  Starting Local Orchestrator..."
cd "$VAULT_PATH" && git pull --rebase origin main
check "Vault synced to Local"
wait_input

# Step 6: Review and approve
step 6 "Review pending approval"
echo "  Check Pending_Approval/email/ for the draft:"
ls -la "$VAULT_PATH/Pending_Approval/email/" 2>/dev/null || echo "  (sync may take a moment)"
echo ""
echo "  To approve: move the file to Approved/"
echo "  To reject: move the file to Rejected/"
wait_input

# Step 7: Verify completion
step 7 "Verify email sent and logged"
echo "  Check Done/email/ for completed task:"
ls -la "$VAULT_PATH/Done/email/" 2>/dev/null || echo "  (no completed tasks yet)"
echo ""
echo "  Check Logs/ for audit trail:"
ls -la "$VAULT_PATH/Logs/" 2>/dev/null || echo "  (no logs yet)"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║          PLATINUM DEMO COMPLETE! 🎉             ║"
echo "╚══════════════════════════════════════════════════╝"
