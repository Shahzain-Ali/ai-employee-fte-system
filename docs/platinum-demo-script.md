# Platinum Demo Script — Hackathon Judges

## Setup (Before Demo)
- Cloud VM running (Oracle ARM A1, 24/7)
- Local laptop with WSL2
- Gmail account configured

## Demo Flow (5-7 minutes)

### Step 1: Show Cloud VM is Running (30s)
```bash
ssh ubuntu@<VM_IP> "pm2 status"
```
**Talk**: "Cloud VM is running 24/7 on Oracle Free Tier — email watcher, orchestrator, gitwatch, health monitor."

### Step 2: Turn OFF Local Agent (15s)
**Talk**: "Local laptop orchestrator is OFF. The Cloud agent works independently."

### Step 3: Send Test Email (30s)
Send email to your Gmail: "Quote request for 100 units of Widget X"
**Talk**: "Customer sends an email. Our laptop is off, but the Cloud agent is watching."

### Step 4: Watch Cloud Process (1-2 min)
```bash
ssh ubuntu@<VM_IP> "tail -f /var/log/fte/cloud-orchestrator.log"
```
**Talk**: "Cloud agent detected the email, triaged it, and created a draft reply. It can NOT send — only draft."

### Step 5: Show Draft in Vault (30s)
```bash
ssh ubuntu@<VM_IP> "ls ~/vault/Pending_Approval/email/"
ssh ubuntu@<VM_IP> "cat ~/vault/Pending_Approval/email/*.md"
```
**Talk**: "Draft is in Pending_Approval — waiting for human approval."

### Step 6: Start Local & Approve (1 min)
```bash
bash scripts/start-local.sh
ls ~/vault/Pending_Approval/email/
# Move to Approved/
mv ~/vault/Pending_Approval/email/*.md ~/vault/Approved/
```
**Talk**: "Local agent starts, syncs vault, sees pending approval. Owner reviews and approves."

### Step 7: Verify Email Sent (30s)
Check Gmail sent folder.
```bash
ls ~/vault/Done/email/
cat ~/vault/Logs/$(date +%Y-%m-%d).json | tail -5
```
**Talk**: "Email sent! Audit trail complete. Cloud drafted, Local approved and sent."

## Key Points for Judges
- **24/7 operation** — works while laptop is off
- **Human-in-the-loop** — Cloud can only draft, human must approve
- **Security** — credentials split, sensitive data local-only
- **Zero cost** — Oracle Free Tier, no ongoing charges
