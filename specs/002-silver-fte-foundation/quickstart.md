# Quickstart: Silver Tier — Functional Assistant

**Feature**: 002-silver-fte-foundation
**Prerequisites**: Bronze tier fully implemented and working

---

## Overview

Silver tier extends Bronze with:
- Gmail Watcher (OAuth2)
- WhatsApp Watcher (Playwright)
- LinkedIn Automation (Playwright)
- Email MCP Server
- Task Scheduling (APScheduler)
- Enhanced Dashboard

---

## Step 1: Install Silver Dependencies

```bash
# Navigate to project
cd /mnt/e/hackathon-0/full-time-equivalent-project

# Install Silver tier dependencies
uv add google-api-python-client google-auth-oauthlib google-auth-httplib2
uv add playwright playwright-stealth
uv add APScheduler SQLAlchemy
uv add mcp

# Install Playwright browsers
playwright install chromium
```

---

## Step 2: Gmail Setup

### 2.1 Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project: `AI-Employee-Silver`
3. Enable Gmail API:
   - APIs & Services → Library
   - Search "Gmail API" → Enable

### 2.2 OAuth2 Credentials

1. APIs & Services → Credentials
2. Create Credentials → OAuth client ID
3. Application type: Desktop app
4. Name: `AI Employee Gmail`
5. Download JSON → Save as `credentials.json`

### 2.3 Store Credentials

```bash
# Create secrets directory (excluded from git)
mkdir -p .secrets

# Move credentials
mv ~/Downloads/credentials.json .secrets/gmail_credentials.json

# Update .env
echo 'GMAIL_CREDENTIALS_PATH=.secrets/gmail_credentials.json' >> .env
echo 'GMAIL_TOKEN_PATH=.secrets/gmail_token.json' >> .env
```

### 2.4 First-time Authorization

```bash
# Run Gmail watcher once to authorize
python src/watchers/gmail_watcher.py --authorize

# Browser opens → Login → Grant permissions
# Token saved to .secrets/gmail_token.json
```

---

## Step 3: WhatsApp Setup

### 3.1 Session Directory

```bash
# Create persistent session directory
mkdir -p .sessions/whatsapp
```

### 3.2 First-time Login

```bash
# Run WhatsApp watcher in visible mode
python src/watchers/whatsapp_watcher.py --setup

# Browser opens WhatsApp Web
# Scan QR code with your phone
# Session saved to .sessions/whatsapp/
```

### 3.3 Configure Keywords

```bash
# Update .env with keywords
echo 'WHATSAPP_KEYWORDS=urgent,asap,invoice,payment,help' >> .env
```

---

## Step 4: LinkedIn Setup

### 4.1 Session Directory

```bash
mkdir -p .sessions/linkedin
```

### 4.2 First-time Login

```bash
# Run LinkedIn setup
python src/watchers/linkedin_poster.py --setup

# Browser opens LinkedIn
# Login manually (handle 2FA if enabled)
# Session saved to .sessions/linkedin/
```

---

## Step 5: MCP Server Setup

### 5.1 Create MCP Configuration

```bash
# Create MCP config directory
mkdir -p ~/.config/claude-code

# Create mcp.json
cat > ~/.config/claude-code/mcp.json << 'EOF'
{
  "servers": [
    {
      "name": "email",
      "command": "python",
      "args": ["src/mcp/email_server.py"],
      "env": {
        "GMAIL_CREDENTIALS": ".secrets/gmail_credentials.json",
        "GMAIL_TOKEN": ".secrets/gmail_token.json"
      }
    }
  ]
}
EOF
```

### 5.2 Test MCP Server

```bash
# Start MCP server manually to test
python src/mcp/email_server.py

# Should output: "Email MCP server running..."
```

---

## Step 6: Scheduler Setup

### 6.1 Create Schedule Config

```bash
cat > config/schedules.json << 'EOF'
{
  "schedules": [
    {
      "id": "gmail_morning",
      "task": "check_gmail",
      "cron": "0 9 * * *",
      "enabled": true,
      "description": "Check Gmail every day at 9 AM"
    },
    {
      "id": "whatsapp_frequent",
      "task": "check_whatsapp",
      "interval_minutes": 30,
      "enabled": true,
      "description": "Check WhatsApp every 30 minutes"
    },
    {
      "id": "linkedin_weekly",
      "task": "generate_linkedin_post",
      "cron": "0 10 * * 1",
      "enabled": true,
      "description": "Generate LinkedIn post every Monday 10 AM"
    }
  ]
}
EOF
```

---

## Step 7: Create Silver Agent Skills

### 7.1 Email Responder Skill

```bash
cat > .claude/skills/email_responder.md << 'EOF'
# Skill: Email Responder

## Purpose
Process incoming email action files and draft appropriate responses.

## Platform
email

## Trigger
EMAIL_*.md file in Needs_Action/

## Inputs
- action_file: Path to EMAIL_*.md file

## Steps
1. Read email content from action file
2. Analyze intent and urgency
3. Check if sender is in approved contacts
4. Draft response based on content
5. If response needed, create approval request
6. Move action file to Done/

## Approval Required
- Replies to unknown contacts: always
- Replies to known contacts: if amount mentioned > $100

## Output
- If reply needed: Approval file in Pending_Approval/
- Updated action file in Done/
- Log entry in Logs/

## Logging
Log: sender, subject, action taken, approval status

## Error Handling
If email cannot be parsed, move to Done/ with error note.
EOF
```

### 7.2 Create remaining skills

```bash
# WhatsApp Handler
cat > .claude/skills/whatsapp_handler.md << 'EOF'
# Skill: WhatsApp Handler

## Purpose
Process incoming WhatsApp messages and suggest responses.

## Platform
whatsapp

## Trigger
WA_*.md file in Needs_Action/

## Inputs
- action_file: Path to WA_*.md file

## Steps
1. Read message content
2. Identify keywords that triggered
3. Determine urgency level
4. Suggest response or action
5. Create approval request if reply needed
6. Move to Done/

## Approval Required
All replies require approval.

## Output
- Approval file if reply needed
- Action file moved to Done/

## Logging
Log: sender, keywords, suggested action, approval status
EOF

# LinkedIn Poster
cat > .claude/skills/linkedin_poster.md << 'EOF'
# Skill: LinkedIn Poster

## Purpose
Generate LinkedIn post content for business promotion.

## Platform
linkedin

## Trigger
Manual request or weekly schedule

## Inputs
- topic: Optional topic focus
- style: professional | casual | technical

## Steps
1. Research recent company activities
2. Draft post content (2-3 paragraphs)
3. Add relevant hashtags
4. Create approval request with preview
5. Wait for approval
6. Post via Playwright upon approval

## Approval Required
All posts require approval.

## Output
- Draft in Pending_Approval/
- Published post upon approval

## Logging
Log: post content, approval status, post URL if published
EOF

# Plan Creator
cat > .claude/skills/plan_creator.md << 'EOF'
# Skill: Plan Creator

## Purpose
Create Plan.md for complex multi-step tasks.

## Platform
general

## Trigger
Task requiring 3+ steps detected

## Inputs
- task_description: What needs to be done
- source_file: Optional triggering action file

## Steps
1. Analyze task complexity
2. Break into discrete steps
3. Identify steps requiring approval
4. Create PLAN_*.md with checkboxes
5. Begin executing first step

## Approval Required
Not for plan creation; individual steps may require approval.

## Output
- Plan.md in Plans/ folder

## Logging
Log: plan created, steps count, approval requirements
EOF

# Approval Checker
cat > .claude/skills/approval_checker.md << 'EOF'
# Skill: Approval Checker

## Purpose
Process approved actions from Approved/ folder.

## Platform
general

## Trigger
File detected in Approved/

## Inputs
- approval_file: Path to approved action file

## Steps
1. Read approval file details
2. Identify action type (email, linkedin, etc.)
3. Execute approved action via appropriate tool
4. Log execution result
5. Move files to Done/

## Approval Required
N/A - actions already approved.

## Output
- Executed action
- Files moved to Done/

## Logging
Log: action type, execution result, any errors
EOF
```

---

## Step 8: Update Vault Structure

```bash
# Add Plans folder to vault
mkdir -p AI_Employee_Vault/Plans

# Add state directory
mkdir -p .state
```

---

## Step 9: Test Individual Components

### 9.1 Test Gmail Watcher

```bash
# Run Gmail watcher once
python src/watchers/gmail_watcher.py --once

# Send yourself an important email
# Check Needs_Action/ for EMAIL_*.md
```

### 9.2 Test WhatsApp Watcher

```bash
# Run WhatsApp watcher once
python src/watchers/whatsapp_watcher.py --once

# Send WhatsApp message with "urgent"
# Check Needs_Action/ for WA_*.md
```

### 9.3 Test Approval Workflow

```bash
# Create test approval file
cat > AI_Employee_Vault/Pending_Approval/TEST_approval.md << 'EOF'
---
type: approval_request
action: test
status: pending
---

## Test Action

This is a test approval.

## To Approve
Move to /Approved/ folder.
EOF

# Move to Approved/
mv AI_Employee_Vault/Pending_Approval/TEST_approval.md AI_Employee_Vault/Approved/

# Check logs for approval execution
```

---

## Step 10: Start Full System

### 10.1 Update PM2 Ecosystem

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'orchestrator',
      script: 'python',
      args: 'src/main.py',
      autorestart: true
    },
    {
      name: 'gmail-watcher',
      script: 'python',
      args: 'src/watchers/gmail_watcher.py',
      autorestart: true
    },
    {
      name: 'whatsapp-watcher',
      script: 'python',
      args: 'src/watchers/whatsapp_watcher.py',
      autorestart: true
    },
    {
      name: 'inbox-watcher',
      script: 'python',
      args: 'src/watchers/filesystem_watcher.py',
      autorestart: true
    }
  ]
}
```

### 10.2 Start All Processes

```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Enable on boot
```

---

## Step 11: Verify Dashboard

Open `AI_Employee_Vault/Dashboard.md` in Obsidian.

Should show:
- Watcher status table (all Running)
- Platform stats
- Pending approvals count
- Recent activity

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Gmail auth fails | Delete token.json, re-authorize |
| WhatsApp session expired | Run --setup again, scan QR |
| LinkedIn blocked | Use stealth mode, add delays |
| MCP not connecting | Check mcp.json path, restart Claude Code |
| Scheduler not running | Check jobs.db exists, verify cron syntax |

---

## Security Checklist

- [ ] .secrets/ in .gitignore
- [ ] .sessions/ in .gitignore
- [ ] .state/ in .gitignore
- [ ] credentials.json not in vault
- [ ] token.json not in vault
- [ ] No passwords in config files

---

## Next Steps

1. Run system for 24 hours
2. Review Dashboard for issues
3. Tune keyword list based on false positives
4. Adjust schedule times as needed
5. Add more Agent Skills as needed
