# Data Model: Platinum Tier — Always-On Cloud + Local Executive

**Feature**: 004-platinum-cloud-local
**Date**: 2026-03-09

---

## Vault Folder Structure (Primary Data Model)

The vault uses **file location as state** — task status is encoded by which folder the
file resides in, not by file content.

```
vault/
├── Needs_Action/
│   ├── email/              # New emails needing response
│   ├── social/             # Social media items needing action
│   ├── invoice/            # Invoice/accounting tasks
│   └── general/            # Other tasks
├── In_Progress/
│   ├── cloud/              # Tasks claimed by Cloud Agent
│   └── local/              # Tasks claimed by Local Agent
├── Plans/
│   ├── email/              # Email response plans
│   ├── social/             # Social media plans
│   └── invoice/            # Financial plans
├── Pending_Approval/
│   ├── email/              # Draft email replies awaiting approval
│   ├── social/             # Draft social posts awaiting approval
│   └── invoice/            # Draft invoices awaiting approval
├── Updates/
│   └── cloud_status_<ts>.md  # Cloud Agent status updates (read by Local)
├── Done/
│   ├── email/              # Completed email tasks
│   ├── social/             # Completed social tasks
│   └── invoice/            # Completed invoice tasks
├── Logs/
│   └── YYYY-MM-DD.json     # Daily structured audit logs
├── Briefings/
│   └── ceo_briefing_YYYY-MM-DD.md  # Weekly CEO briefings
└── Dashboard.md            # Single-writer: Local Agent only
```

---

## Entity: Task File (Markdown)

A task file is a markdown document that moves through the vault folder structure.

**Filename Pattern**: `<domain>_<action>_<id>_<timestamp>.md`
Example: `email_reply_client001_20260309T140000.md`

**Required Fields (YAML frontmatter):**

```yaml
---
id: <unique-id>
type: email_reply | social_post | invoice_create | general_task
domain: email | social | invoice | general
created_by: cloud | local
created_at: 2026-03-09T14:00:00Z
claimed_by: null | cloud | local
claimed_at: null | 2026-03-09T14:01:00Z
status: needs_action | in_progress | pending_approval | approved | done | rejected
priority: low | medium | high | urgent
---
```

**Body Content (varies by type):**

For email_reply:
```markdown
## Original Email
- From: sender@example.com
- Subject: Quote Request
- Received: 2026-03-09T02:00:00Z

## Draft Reply
[Cloud Agent's drafted response]

## Approval Notes
[Owner's notes after review — filled by Local Agent]
```

**State Transitions:**

```
Needs_Action → In_Progress/<agent> → Pending_Approval → Done
                                  → Plans (if planning needed first)
                                  → Rejected (if owner rejects)
```

---

## Entity: Cloud Status Update

**Location**: `/Updates/cloud_status_<timestamp>.md`
**Purpose**: Cloud Agent reports its activity (since it cannot write Dashboard.md)

```yaml
---
agent: cloud
timestamp: 2026-03-09T14:00:00Z
type: status_update
---

## Actions Since Last Update
- Processed 3 emails (2 drafts created, 1 auto-archived)
- Detected 1 Instagram comment (draft reply created)
- Odoo health: OK

## Pending Approvals
- email_reply_client001_20260309.md (high priority)
- social_post_ig_20260309.md (medium priority)

## Alerts
- None
```

---

## Entity: Health Check Result

**Location**: Cloud VM local file (NOT synced to vault — operational data)
**File**: `/var/log/fte-health/health_<timestamp>.json`

```json
{
  "timestamp": "2026-03-09T14:00:00Z",
  "overall": "healthy",
  "components": {
    "odoo": { "status": "up", "response_ms": 120 },
    "email_watcher": { "status": "up", "pid": 1234 },
    "orchestrator": { "status": "up", "pid": 1235 },
    "git_sync": { "status": "up", "last_push": "2026-03-09T13:58:00Z" },
    "disk": { "status": "ok", "usage_percent": 45 },
    "ram": { "status": "ok", "usage_percent": 62 }
  },
  "alerts": []
}
```

---

## Entity: PM2 Ecosystem Config

**Location**: Cloud VM `/home/ubuntu/ecosystem.config.js`

```
Processes managed:
- email-watcher        (Python: src/watchers/gmail_watcher.py)
- orchestrator         (Python: src/orchestrator/orchestrator.py)
- health-monitor       (Python/Bash: scripts/health-monitor.sh)
- gitwatch             (Bash: gitwatch -r origin -b main /path/to/vault)
- git-pull-cron        (handled by system cron, not PM2)
```

---

## Entity: Agent Configuration

Each agent (Cloud/Local) has its own config defining its zone permissions.

**Cloud Agent Config** (`cloud-agent.yaml`):
```yaml
agent: cloud
zone: draft-only
allowed_actions:
  - read_email
  - triage_email
  - draft_reply
  - draft_social_post
  - draft_invoice
  - read_odoo
  - suggest_schedule
forbidden_actions:
  - send_email
  - publish_social
  - confirm_payment
  - write_dashboard
  - access_whatsapp
  - access_banking
model_config:
  primary: claude-sonnet-4-6      # Token-efficient for routine processing
  complex: claude-opus-4-6        # For complex reasoning when needed
  fallback: minimax:m2.5:cloud    # Via Ollama when paid limits exhausted
```

**Local Agent Config** (`local-agent.yaml`):
```yaml
agent: local
zone: full-access
allowed_actions:
  - all  # Full permissions
  - approve_drafts
  - send_email
  - publish_social
  - confirm_payment
  - write_dashboard
  - access_whatsapp
  - access_banking
model_config:
  primary: claude-sonnet-4-6      # Token-efficient for routine processing
  complex: claude-opus-4-6        # For complex reasoning when needed
  fallback: minimax:m2.5:cloud    # Via Ollama when paid limits exhausted
```

---

## Entity: Credential Split

**Cloud VM `.env`:**
```
# API access (read + draft capabilities)
ANTHROPIC_API_KEY=sk-ant-...
GMAIL_CREDENTIALS_PATH=/home/ubuntu/.credentials/gmail.json
META_PAGE_ACCESS_TOKEN=...
META_IG_ACCESS_TOKEN=...
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=...

# Git sync
GITHUB_SSH_KEY=/home/ubuntu/.ssh/id_ed25519
VAULT_PATH=/home/ubuntu/vault
```

**Local `.env` (contains ALL including sensitive):**
```
# Everything Cloud has PLUS:
WHATSAPP_SESSION_PATH=...
BANKING_CREDENTIALS=...
PERSONAL_API_TOKENS=...
```

**Key Rule**: Cloud `.env` and Local `.env` are INDEPENDENT files.
They are NEVER synced via Git. Each is maintained separately.
