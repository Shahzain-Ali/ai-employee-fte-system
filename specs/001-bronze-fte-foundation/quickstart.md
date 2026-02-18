# Quickstart Guide: Bronze Tier — Personal AI Employee Foundation

**Feature**: 001-bronze-fte-foundation
**Date**: 2026-02-17
**Prerequisites**: Windows 11 + WSL2 (Ubuntu 24.04), Python 3.14.3, Node.js v24+

---

## Overview

This guide walks you through setting up the Bronze tier Personal AI Employee system. By the end, you'll have:

1. A structured Obsidian vault (the AI's workspace)
2. A File System Watcher monitoring Inbox/ for new files
3. An Orchestrator triggering Claude Code for processing
4. Agent Skills defining all AI behavior
5. Full audit logging for accountability

---

## Step 1: Prerequisites Check

### Required Software

```bash
# Check Python version (must be 3.14+)
python3.14 --version

# Check Node.js version (must be v24+)
node --version

# Check Claude Code is installed
claude --version

# Check uv is installed
uv --version
```

### Install Missing Dependencies

```bash
# Install uv (if not present)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install PM2 globally (for process management)
npm install -g pm2
```

---

## Step 2: Project Setup

### Clone and Initialize

```bash
# Navigate to your project directory
cd /mnt/e/hackathon-0/full-time-equivalent-project

# Create Python virtual environment with uv
uv venv --python 3.14

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install watchdog python-dotenv

# Install dev dependencies
uv pip install pytest pytest-asyncio
```

### Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your paths
nano .env
```

**.env contents:**

```env
# Vault Configuration
VAULT_PATH=/mnt/e/hackathon-0/full-time-equivalent-project/AI_Employee_Vault

# Watcher Settings
POLL_INTERVAL=60

# Claude Code Settings
CLAUDE_TIMEOUT=300

# Safety Mode (set to false for production)
DRY_RUN=true
```

---

## Step 3: Create Vault Structure

### Run Vault Initialization

The vault will be created automatically when you first run the system, but you can create it manually:

```bash
# Create vault directory structure
mkdir -p AI_Employee_Vault/{Inbox,Needs_Action,Done,Logs,Pending_Approval,Approved,Rejected}

# Verify structure
ls -la AI_Employee_Vault/
```

### Expected Output

```
AI_Employee_Vault/
├── Inbox/              # Drop files here for processing
├── Needs_Action/       # Watcher creates action files here
├── Done/               # Completed tasks moved here
├── Logs/               # JSON audit logs (YYYY-MM-DD.json)
├── Pending_Approval/   # Sensitive actions waiting for approval
├── Approved/           # Owner-approved actions
└── Rejected/           # Owner-rejected actions
```

---

## Step 4: Create Core Vault Files

### Dashboard.md

Create `AI_Employee_Vault/Dashboard.md`:

```markdown
# AI Employee Dashboard

**Last Updated**: Not yet initialized
**Status**: Idle

## Current Stats

| Metric | Value |
|--------|-------|
| Pending Tasks | 0 |
| Awaiting Approval | 0 |
| Completed Today | 0 |

## Recent Activity

_No activity recorded yet._

## Pending Approvals

_No approvals pending._
```

### Company_Handbook.md

Create `AI_Employee_Vault/Company_Handbook.md`:

```markdown
# Company Handbook — AI Employee Guidelines

## Identity

- **Name**: AI Employee (Bronze Tier)
- **Role**: Personal Assistant
- **Owner**: [Your Name]
- **Active Since**: 2026-02-17

## Working Hours

This AI Employee operates 24/7 when the watcher and orchestrator are running.

## Approval Requirements

The following actions ALWAYS require human approval:

1. **Payments** — Any payment of any amount
2. **Emails** — Sending to contacts not in the approved list
3. **File Deletions** — Deleting any file from the vault

## Forbidden Actions

The AI Employee must NEVER:

- Access credentials or API keys directly
- Execute .exe, .bat, .sh, or other executable files
- Send data outside the local machine
- Modify this Handbook without approval
- Skip the approval workflow for sensitive actions

## Response Guidelines

- Be concise and professional
- Use markdown formatting in all outputs
- Always log actions to Logs/YYYY-MM-DD.json
- Update Dashboard.md after completing any task

## Escalation Rules

Immediately alert the owner (via Dashboard.md) when:

- An error occurs 3 times in a row
- An unknown file type is detected
- The orchestrator has been waiting > 10 minutes

## Approved Contacts

_Empty — all email recipients require approval in Bronze tier._
```

---

## Step 5: Create Agent Skills

### Directory Setup

```bash
mkdir -p .claude/skills
```

### process_document.md

Create `.claude/skills/process_document.md`:

```markdown
# Skill: Process Document

## Purpose

Handle incoming documents dropped in Inbox/ and create appropriate action records.

## Inputs

- action_file_path: Path to the action file in Needs_Action/

## Steps

1. Read the action file YAML frontmatter
2. Read Company_Handbook.md for processing rules
3. Analyze the original file in Inbox/ (if still present)
4. Determine required actions based on file type:
   - PDF: Extract metadata, categorize
   - Image: Note dimensions, suggest tagging
   - Document: Summarize content
5. Update action file status to "completed"
6. Move action file to Done/
7. Log the completion

## Output

- Updated action file in Done/
- Log entry in Logs/YYYY-MM-DD.json
- Dashboard.md updated with activity

## Logging

Log entry must include:
- action_type: "processing_completed"
- source: "claude_code"
- target_file: Done/ path
- skill_used: "process_document"
- duration_ms: processing time

## Error Handling

1. If file cannot be read: Mark status as "failed", log error
2. If processing exceeds 5 minutes: Log timeout warning
3. If unknown file type: Create REJECTED_ action file with reason
```

### update_dashboard.md

Create `.claude/skills/update_dashboard.md`:

```markdown
# Skill: Update Dashboard

## Purpose

Refresh Dashboard.md with current vault statistics and recent activity.

## Inputs

None — reads vault state directly.

## Steps

1. Count files in Needs_Action/ → pending_count
2. Count files in Pending_Approval/ → approval_count
3. Count today's files in Done/ → completed_today
4. Read last 5 entries from today's log file
5. List all files in Pending_Approval/ with links
6. Update Dashboard.md placeholders:
   - {{LAST_UPDATED}}: current ISO timestamp
   - {{STATUS}}: Idle/Working/Waiting for Approval
   - {{PENDING_COUNT}}: pending_count
   - {{APPROVAL_COUNT}}: approval_count
   - {{COMPLETED_TODAY}}: completed_today
   - {{RECENT_ACTIVITY}}: formatted log entries
   - {{PENDING_APPROVALS}}: file links

## Output

- Updated Dashboard.md file

## Logging

Log entry must include:
- action_type: "dashboard_updated"
- source: "claude_code"
- details: { pending_count, approval_count, completed_today }

## Error Handling

1. If log file doesn't exist: Show "No activity recorded"
2. If counts fail: Show "Error counting" and log issue
```

### create_approval_request.md

Create `.claude/skills/create_approval_request.md`:

```markdown
# Skill: Create Approval Request

## Purpose

Generate a HITL approval file for sensitive actions that require human decision.

## Inputs

- action_type: "payment" | "email_send" | "file_delete"
- source_file: Path to original action file
- reason: Why approval is needed
- details: Action-specific details object

## Steps

1. Validate action_type is in allowed list
2. Generate filename: APPROVAL_<action_type>_<timestamp>.md
3. Create YAML frontmatter with all required fields
4. Write human-readable body explaining:
   - What action is being requested
   - Why it requires approval
   - What happens if approved
   - What happens if rejected
5. Save file to Pending_Approval/
6. Update Dashboard.md to show pending approval
7. Log the approval request

## Output

- Approval file in Pending_Approval/
- Updated Dashboard.md
- Log entry

## Logging

Log entry must include:
- action_type: "approval_requested"
- source: "claude_code"
- target_file: Pending_Approval/ path
- approval_status: "pending"
- details: { action_type, reason }

## Error Handling

1. If invalid action_type: Reject with error log
2. If source_file doesn't exist: Log warning, proceed with available info
3. If Pending_Approval/ is full (>10 files): Log warning to Dashboard
```

---

## Step 6: Start the System

### Start Watcher and Orchestrator with PM2

```bash
# Start the file system watcher
pm2 start src/main.py --name "fte-watcher" --interpreter python3.14

# Check status
pm2 status

# View logs
pm2 logs fte-watcher
```

### Configure PM2 Startup (Optional)

```bash
# Generate startup script (survives reboot)
pm2 startup

# Save current process list
pm2 save
```

---

## Step 7: Test the System

### Test 1: File Drop Detection

```bash
# Drop a test file into Inbox/
cp /path/to/sample.pdf AI_Employee_Vault/Inbox/

# Wait 60 seconds, then check Needs_Action/
ls AI_Employee_Vault/Needs_Action/
# Expected: FILE_sample.pdf.md

# Check the log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
```

### Test 2: Verify Dashboard Update

Open `AI_Employee_Vault/Dashboard.md` in Obsidian. You should see:

- Pending Tasks: 1
- Recent Activity showing file detection

### Test 3: Rejected File Type

```bash
# Drop an executable (should be rejected)
touch AI_Employee_Vault/Inbox/test.exe

# Wait 60 seconds, check Needs_Action/
ls AI_Employee_Vault/Needs_Action/
# Expected: REJECTED_test.exe.md
```

### Test 4: Crash Recovery

```bash
# Kill the watcher
pm2 stop fte-watcher

# Wait 60 seconds
pm2 status
# Watcher should auto-restart
```

---

## Troubleshooting

### Watcher Not Detecting Files

1. Check if watcher is running: `pm2 status`
2. Verify VAULT_PATH in .env is correct
3. Check permissions: `ls -la AI_Employee_Vault/Inbox/`
4. Review logs: `pm2 logs fte-watcher --lines 50`

### Claude Code Not Triggering

1. Verify Claude Code is installed: `claude --version`
2. Check orchestrator logs: `pm2 logs fte-orchestrator`
3. Verify DRY_RUN is set to `false` in .env

### Approval Flow Not Working

1. Ensure file was moved (not copied) to Approved/
2. Check that original file is removed from Pending_Approval/
3. Review approval file YAML for correct format

---

## Next Steps

After Bronze tier is working:

1. **Monitor**: Watch Dashboard.md in Obsidian for activity
2. **Customize**: Edit Company_Handbook.md to adjust rules
3. **Extend**: Add new Agent Skills for specific tasks
4. **Upgrade**: Proceed to Silver tier for Gmail/WhatsApp integration

---

## File Reference

| File | Purpose |
|------|---------|
| `.env` | Configuration (paths, timeouts) |
| `AI_Employee_Vault/Dashboard.md` | Real-time status view |
| `AI_Employee_Vault/Company_Handbook.md` | AI behavior rules |
| `.claude/skills/*.md` | Agent Skill definitions |
| `Logs/YYYY-MM-DD.json` | Audit logs |
| `src/main.py` | Entry point |
| `src/watchers/filesystem_watcher.py` | Inbox monitor |
| `src/orchestrator/orchestrator.py` | Claude trigger |
