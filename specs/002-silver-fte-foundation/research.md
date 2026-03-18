# Research: Silver Tier Technology Decisions

**Feature**: 002-silver-fte-foundation
**Date**: 2026-02-18
**Status**: Complete

---

## 1. Gmail API Integration

### Decision: Use `google-api-python-client` with OAuth2

**Rationale**:
- Official Google library for Gmail API
- OAuth2 handles authentication securely
- Supports automatic token refresh
- Explicitly shown in hackathon documentation (Page 7-8)

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| `google-api-python-client` | Official, full-featured | Complex OAuth setup | ✅ Selected |
| `imaplib` (IMAP) | Built-in Python | Less secure, no labels | OAuth2 preferred |
| `yagmail` | Simpler API | Send-only, not for reading | Need to read emails |
| Third-party email services | Hosted | Not local-first | Constitution Principle I |

**Required Packages**:
```
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.2.0
```

**OAuth2 Credential Flow**:
1. Create Google Cloud project
2. Enable Gmail API
3. Create OAuth2 credentials (Desktop app)
4. Download `credentials.json`
5. First run: browser opens for consent
6. Token saved to `token.json` (auto-refresh)

---

## 2. WhatsApp Web Automation

### Decision: Use Playwright with persistent context

**Rationale**:
- Free (no Twilio/API costs)
- Session persistence via `launch_persistent_context`
- Browser automation handles WhatsApp Web directly
- Explicitly recommended in hackathon documentation (Pages 8-9)

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Playwright | Free, session persistence, stealth | ToS concerns | ✅ Selected (hackathon recommends) |
| Twilio WhatsApp API | Official, reliable | $$$, business account needed | Too expensive |
| WhatsApp Business API | Official | Complex setup, approval needed | Not for personal use |
| Selenium | Familiar | Slower, less stealth features | Playwright is modern |

**Session Persistence**:
```python
browser = playwright.chromium.launch_persistent_context(
    user_data_dir="/path/to/whatsapp_session",
    headless=False  # QR scan needs visible browser first time
)
```

**Keyword Filtering**:
- Default keywords: `['urgent', 'asap', 'invoice', 'payment', 'help']`
- Configurable via `.env` or config file

**ToS Warning**: Documentation states "Be aware of WhatsApp's terms of service"

---

## 3. LinkedIn Automation

### Decision: Use Playwright with stealth mode

**Rationale**:
- Browser automation for posting
- `playwright-stealth` reduces bot detection
- Random delays simulate human behavior
- Hackathon documentation shows this approach

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Playwright + stealth | Full control, free | Bot detection risk | ✅ Selected |
| LinkedIn API | Official | Limited posting, approval needed | Not for automation |
| Third-party schedulers | Easy | Not local-first, paid | Constitution Principle I |
| Manual posting | No risk | Not automated | Defeats purpose |

**Stealth Configuration**:
```python
from playwright_stealth import stealth_sync

page = browser.new_page()
stealth_sync(page)

# Random delays
import random
await page.wait_for_timeout(random.randint(2000, 5000))
```

**Required Packages**:
```
playwright>=1.40.0
playwright-stealth>=1.0.6
```

---

## 4. MCP Server for Email

### Decision: Build custom MCP server using `mcp` Python package

**Rationale**:
- MCP (Model Context Protocol) is standard for Claude tools
- Python SDK available: `mcp`
- Can wrap Gmail API for send_email functionality
- Hackathon documentation shows MCP configuration (Page 10)

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Custom Python MCP | Full control, Python ecosystem | Build effort | ✅ Selected |
| Node.js MCP | JS ecosystem | Different language | Python consistency |
| Pre-built email-mcp | Ready to use | May not exist/fit needs | Custom is reliable |

**MCP Server Structure**:
```python
from mcp.server import Server
from mcp.types import Tool

server = Server("email-mcp")

@server.tool("send_email")
async def send_email(to: str, subject: str, body: str, attachment: str = None):
    # Use Gmail API to send
    pass
```

**MCP Configuration** (`~/.config/claude-code/mcp.json`):
```json
{
  "servers": [
    {
      "name": "email",
      "command": "python",
      "args": ["/path/to/email_mcp_server.py"],
      "env": { "GMAIL_CREDENTIALS": "/path/to/credentials.json" }
    }
  ]
}
```

---

## 5. Task Scheduling

### Decision: Use APScheduler with SQLite persistence

**Rationale**:
- Pure Python, no external process needed
- SQLite jobstore persists jobs across restarts
- Integrates into orchestrator.py
- Cron-style expressions supported

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| APScheduler | Python native, persistence | Requires running process | ✅ Selected |
| Windows Task Scheduler | OS-level, reliable | Separate from Python | Split management |
| Cron (Linux) | Standard | Linux-only | Not cross-platform |
| Celery | Full-featured | Overkill, needs broker | Too complex |

**Hybrid Approach (Recommended)**:
1. Windows Task Scheduler starts orchestrator.py on boot
2. APScheduler inside orchestrator handles all scheduled tasks
3. Best of both: auto-start + Python control

**Persistence Configuration**:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
}

scheduler = BackgroundScheduler(jobstores=jobstores)
```

**Required Packages**:
```
APScheduler>=3.10.0
SQLAlchemy>=2.0.0
```

---

## 6. Human-in-the-Loop Approval

### Decision: File-based workflow with folder watching

**Rationale**:
- Extends Bronze tier approach
- Owner moves files between folders in Obsidian
- Orchestrator watches Approved/ folder
- Simple, reliable, no new technology needed

**Folder Structure**:
```
AI_Employee_Vault/
├── Pending_Approval/    # Sensitive actions waiting
├── Approved/            # Owner approved - execute
└── Rejected/            # Owner rejected - log & close
```

**Approval File Format**:
```markdown
---
type: approval_request
action: send_email | linkedin_post | payment
status: pending
created_at: 2026-02-18T10:00:00Z
---

## Action Details
[Details specific to action type]

## To Approve
Move this file to `/Approved/` folder.

## To Reject
Move this file to `/Rejected/` folder.
```

---

## 7. Claude Reasoning Loop (Plan.md)

### Decision: Claude creates Plan.md with markdown checkboxes

**Rationale**:
- Makes AI reasoning transparent
- Owner can review/modify plan before execution
- Simple markdown format, works in Obsidian
- Hackathon documentation shows this pattern (Page 9)

**Plan.md Format**:
```markdown
# Plan: [Task Name]

Created: [timestamp]
Status: in_progress | completed | blocked

## Steps

- [x] Step 1: Completed step
- [ ] Step 2: Pending step (REQUIRES APPROVAL)
- [ ] Step 3: Future step

## Notes
[Claude's reasoning and observations]
```

**Storage Location**: `AI_Employee_Vault/Plans/PLAN_{task_slug}_{date}.md`

---

## 8. Enhanced Dashboard

### Decision: Extend Bronze Dashboard with watcher status

**Rationale**:
- Build on existing Dashboard.md
- Add watcher status table
- Add platform-specific stats
- Single source for system health

**New Dashboard Sections**:
```markdown
## Watcher Status

| Watcher | Status | Last Check | Today's Count |
|---------|--------|------------|---------------|
| Gmail | Running | 10:30 AM | 5 emails |
| WhatsApp | Running | 10:29 AM | 3 messages |
| Inbox | Running | 10:30 AM | 2 files |

## Platform Stats

| Platform | Processed | Pending | Approved | Rejected |
|----------|-----------|---------|----------|----------|
| Email | 45 | 2 | 12 | 1 |
| WhatsApp | 23 | 1 | 5 | 0 |
| LinkedIn | 8 | 1 | 8 | 0 |
```

---

## 9. Agent Skills (Silver Tier)

### Decision: Add 5 new skills for Silver functionality

**New Skills**:

| Skill | Purpose | Key Actions |
|-------|---------|-------------|
| email_responder.md | Handle incoming emails | Read, categorize, draft reply |
| whatsapp_handler.md | Process WhatsApp messages | Parse, prioritize, suggest response |
| linkedin_poster.md | Generate LinkedIn content | Draft post, create approval request |
| plan_creator.md | Create Plan.md for complex tasks | Decompose task, create checkboxes |
| approval_checker.md | Process approved actions | Watch Approved/, execute actions |

**Skill Template Extension**:
```markdown
# Skill: [Name]

## Purpose
[Description]

## Platform
[email | whatsapp | linkedin | general]

## Inputs
- [input_1]: [description]

## Steps
1. [Step]

## Approval Required
[yes/no - if yes, what triggers approval]

## Output
[What this skill produces]
```

---

## 10. Process Management

### Decision: Continue with PM2 (Bronze approach)

**Rationale**:
- Already established in Bronze tier
- Handles multiple processes (orchestrator, watchers)
- Auto-restart on crash
- Startup scripts

**PM2 Ecosystem File** (`ecosystem.config.js`):
```javascript
module.exports = {
  apps: [
    {
      name: 'orchestrator',
      script: 'python',
      args: 'src/main.py',
      watch: false,
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
    }
  ]
}
```

---

## Research Complete

All technology decisions are finalized. No NEEDS CLARIFICATION items remain.

**Summary of New Dependencies (Silver Tier)**:
```toml
[project.dependencies]
# Bronze (existing)
watchdog = ">=4.0.0"
python-dotenv = ">=1.0"

# Silver (new)
google-api-python-client = ">=2.100.0"
google-auth-oauthlib = ">=1.1.0"
google-auth-httplib2 = ">=0.2.0"
playwright = ">=1.40.0"
playwright-stealth = ">=1.0.6"
APScheduler = ">=3.10.0"
SQLAlchemy = ">=2.0.0"
mcp = ">=1.0.0"
```

Proceed with data-model.md and contracts/.
