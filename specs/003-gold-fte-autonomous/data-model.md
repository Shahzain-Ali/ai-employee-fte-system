# Data Model: Gold Tier — Autonomous Employee

**Feature**: 003-gold-fte-autonomous
**Date**: 2026-02-24
**Source**: [spec.md](./spec.md)
**Extends**: [Silver data-model.md](../002-silver-fte-foundation/data-model.md)

---

## Entity Overview

| Entity | Storage | Format | Location | New in Gold |
|--------|---------|--------|----------|-------------|
| Odoo Invoice | Odoo PostgreSQL + Action File | JSON-RPC / YAML+MD | Odoo DB + Needs_Action/ | ✅ New |
| Facebook Page Post | Facebook API + Action File | Graph API / YAML+MD | Facebook + Needs_Action/ | ✅ New |
| Instagram Media | Instagram API + Action File | Graph API / YAML+MD | Instagram + Needs_Action/ | ✅ New |
| CEO Briefing | Markdown | YAML frontmatter + body | Briefings/ | ✅ New |
| Audit Log Entry | JSON | Structured JSON object | Logs/YYYY-MM-DD.json | Extended |
| Cross-Domain Workflow | JSON + Markdown | Workflow state | Logs/ + Action files | ✅ New |
| Ralph Wiggum Task | Markdown | YAML frontmatter + steps | Tasks/ | ✅ New |
| Component Health | JSON | Runtime state | .state/health.json | ✅ New |
| Agent Skill (Gold) | Markdown | Structured procedure | .claude/skills/*.md | Extended |

---

## 1. Odoo Action File

**Purpose**: Represents an Odoo-related action (invoice request, payment confirmation) detected from cross-domain triggers.

**Lifecycle**: Cross-domain trigger → Created in `Needs_Action/` → Orchestrator routes to Odoo skill → MCP server executes → `Done/`

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Always `odoo` | `odoo` |
| action | enum | Yes | `create_invoice`, `mark_paid`, `create_expense` | `create_invoice` |
| partner_name | string | Yes | Client/partner name | `ABC Corp` |
| amount | decimal | No | Amount in currency | `500.00` |
| currency | string | No | ISO currency code | `PKR` |
| due_date | date | No | Invoice due date | `2026-03-15` |
| workflow_id | string | No | Cross-domain workflow link | `wf-abc123` |
| source_trigger | string | No | What triggered this | `EMAIL_18d4a5b2.md` |
| status | enum | Yes | `pending`, `processing`, `completed` | `pending` |
| created_at | datetime | Yes | Creation timestamp | `2026-02-24T10:30:00Z` |

### File Naming Convention

```
ODOO_{action}_{timestamp_compact}.md
```

Example: `ODOO_create_invoice_20260224T103000Z.md`

---

## 2. Facebook Action File

**Purpose**: Represents a Facebook posting/engagement action.

**Lifecycle**: AI decides to post/reply → Approval request → Approved → MCP server posts → `Done/`

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Always `facebook` | `facebook` |
| action | enum | Yes | `create_post`, `reply_comment` | `create_post` |
| page_id | string | Yes | Facebook Page ID | `123456789` |
| message | string | Yes | Post/reply content | `New service available!` |
| post_id | string | No | Target post ID (for replies) | `123_456` |
| comment_id | string | No | Target comment ID (for replies) | `789` |
| workflow_id | string | No | Cross-domain workflow link | `wf-abc123` |
| status | enum | Yes | `pending`, `approved`, `posted`, `failed` | `pending` |
| created_at | datetime | Yes | Creation timestamp | `2026-02-24T10:30:00Z` |

### File Naming Convention

```
FB_{action}_{timestamp_compact}.md
```

Example: `FB_create_post_20260224T103000Z.md`

---

## 3. Instagram Action File

**Purpose**: Represents an Instagram publishing/engagement action.

**Lifecycle**: AI decides to post/reply → Approval request → Approved → MCP server publishes → `Done/`

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Always `instagram` | `instagram` |
| action | enum | Yes | `create_post`, `create_reel`, `reply_comment` | `create_post` |
| ig_user_id | string | Yes | Instagram Business account ID | `17841400123` |
| caption | string | No | Post caption | `Check out our latest...` |
| image_url | string | No | Public image URL | `https://example.com/img.jpg` |
| video_url | string | No | Public video URL | `https://example.com/vid.mp4` |
| media_type | enum | No | `IMAGE`, `VIDEO`, `REELS`, `CAROUSEL_ALBUM` | `IMAGE` |
| comment_id | string | No | Target comment ID (for replies) | `17858893456` |
| reply_message | string | No | Reply text | `Thank you!` |
| workflow_id | string | No | Cross-domain workflow link | `wf-abc123` |
| status | enum | Yes | `pending`, `approved`, `posted`, `failed` | `pending` |
| created_at | datetime | Yes | Creation timestamp | `2026-02-24T10:30:00Z` |

### File Naming Convention

```
IG_{action}_{timestamp_compact}.md
```

Example: `IG_create_post_20260224T103000Z.md`

---

## 4. CEO Briefing

**Purpose**: Weekly business intelligence report combining data from all domains.

**Lifecycle**: APScheduler triggers Sunday night → Collect data from all MCP servers → Generate markdown → Save to `Briefings/`

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Always `ceo_briefing` | `ceo_briefing` |
| week_start | date | Yes | Monday of the week | `2026-02-17` |
| week_end | date | Yes | Sunday of the week | `2026-02-23` |
| generated_at | datetime | Yes | Generation timestamp | `2026-02-23T22:00:00Z` |
| data_sources | array | Yes | Which domains had data | `[odoo, facebook, gmail]` |
| missing_sources | array | No | Unavailable domains | `[instagram]` |
| delayed | boolean | No | Generated after scheduled time | `false` |

### File Naming Convention

```
CEO_Briefing_{YYYY-MM-DD}.md
```

Example: `CEO_Briefing_2026-02-23.md`

### Body Structure

```markdown
---
type: ceo_briefing
week_start: 2026-02-17
week_end: 2026-02-23
generated_at: 2026-02-23T22:00:00Z
data_sources: [odoo, facebook, instagram, gmail, whatsapp]
missing_sources: []
---

# Monday Morning CEO Briefing
## Week of Feb 17 – Feb 23, 2026

## Financial Summary (Odoo)
| Metric | Value |
|--------|-------|
| Revenue | PKR 150,000 |
| Pending Invoices | 3 (PKR 45,000) |
| Expenses | PKR 25,000 |
| Net Profit | PKR 125,000 |

## Social Media (Facebook + Instagram)
| Platform | Posts | Reach | Engagement |
|----------|-------|-------|------------|
| Facebook | 5 | 2,500 | 180 |
| Instagram | 3 | 1,800 | 95 |

## Communications (Gmail + WhatsApp)
- Emails processed: 23
- WhatsApp messages: 15
- Pending responses: 2
- New client contacts: 3

## Action Items
1. Follow up with ABC Corp (invoice overdue 5 days)
2. Instagram engagement dropped 15% — consider more visual content
3. 2 client emails awaiting response

## Proactive Suggestions
- Schedule a Facebook post about recent project completion
- Send payment reminder to XYZ Ltd (due in 3 days)
```

---

## 5. Extended Audit Log Entry (Gold)

**Purpose**: Enhanced structured logging with workflow tracking and duration.

### New Fields (extending Silver)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| workflow_id | string | No | Links related cross-domain actions | `wf-abc123` |
| duration_ms | integer | No | Action execution time | `1250` |
| mcp_server | string | No | Which MCP server handled this | `fte-odoo` |
| retry_count | integer | No | Number of retry attempts | `0` |
| error_message | string | No | Error details (if failed) | `Connection refused` |
| domain | enum | No | `odoo`, `facebook`, `instagram`, `gmail`, `whatsapp` | `odoo` |

### New action_type Values (Gold)

| action_type | Source | Description |
|-------------|--------|-------------|
| `odoo_invoice_created` | fte-odoo MCP | Invoice created in Odoo |
| `odoo_payment_recorded` | fte-odoo MCP | Payment marked received |
| `odoo_expense_created` | fte-odoo MCP | Expense recorded |
| `fb_post_created` | fte-facebook MCP | Post published on Page |
| `fb_comment_replied` | fte-facebook MCP | Reply to comment posted |
| `ig_post_published` | fte-instagram MCP | Image/video published |
| `ig_reel_published` | fte-instagram MCP | Reel published |
| `ig_comment_replied` | fte-instagram MCP | Reply to IG comment |
| `ceo_briefing_generated` | scheduler | Weekly briefing created |
| `workflow_started` | workflow_engine | Cross-domain workflow began |
| `workflow_completed` | workflow_engine | Cross-domain workflow finished |
| `workflow_failed` | workflow_engine | Cross-domain workflow failed |
| `component_health_changed` | health_registry | Component status changed |
| `ralph_wiggum_iteration` | stop_hook | Loop iteration logged |
| `retention_cleanup` | audit_retention | Old logs archived/deleted |

---

## 6. Ralph Wiggum Task File

**Purpose**: Represents a multi-step autonomous task for the Ralph Wiggum loop.

**Lifecycle**: Created in `Tasks/` → Stop hook detects → Claude executes steps → File moves to `Done/` → Loop exits

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Always `ralph_wiggum_task` | `ralph_wiggum_task` |
| task | string | Yes | Task description | `Process invoice and notify client` |
| created_at | datetime | Yes | Creation timestamp | `2026-02-24T10:30:00Z` |
| status | enum | Yes | `pending`, `in_progress`, `completed`, `failed` | `in_progress` |
| max_iterations | integer | Yes | Maximum loop iterations | `10` |
| current_iteration | integer | Yes | Current iteration count | `3` |
| steps_total | integer | Yes | Total steps | `5` |
| steps_completed | integer | Yes | Completed steps | `2` |
| workflow_id | string | No | Link to cross-domain workflow | `wf-abc123` |

### File Naming Convention

```
TASK_{slug}_{YYYYMMDD}.md
```

Example: `TASK_process_invoice_20260224.md`

### Body Structure

```markdown
---
type: ralph_wiggum_task
task: Process invoice request and notify client
status: in_progress
max_iterations: 10
current_iteration: 3
steps_total: 5
steps_completed: 2
---

# Task: Process Invoice Request

## Steps

- [x] Read client email and extract invoice details (completed 10:31)
- [x] Create invoice in Odoo via MCP (completed 10:32)
- [ ] Send invoice to client via email (REQUIRES APPROVAL)
- [ ] Post confirmation on Facebook Page
- [ ] Update Dashboard and log completion

## Context

Client: ABC Corp
Amount: PKR 50,000
Source: EMAIL_18d4a5b2.md
```

---

## 7. Component Health State

**Purpose**: Runtime health status of all system components.

**Location**: `.state/health.json`

### Schema

```json
{
  "components": {
    "odoo": {
      "name": "Odoo (Docker)",
      "status": "healthy",
      "last_check": "2026-02-24T10:30:00Z",
      "last_error": null,
      "consecutive_failures": 0
    },
    "facebook": {
      "name": "Facebook Graph API",
      "status": "healthy",
      "last_check": "2026-02-24T10:30:00Z",
      "last_error": null,
      "consecutive_failures": 0
    },
    "instagram": {
      "name": "Instagram Graph API",
      "status": "healthy",
      "last_check": "2026-02-24T10:30:00Z",
      "last_error": null,
      "consecutive_failures": 0
    },
    "gmail": {
      "name": "Gmail Watcher",
      "status": "healthy",
      "last_check": "2026-02-24T10:30:00Z",
      "last_error": null,
      "consecutive_failures": 0
    },
    "whatsapp": {
      "name": "WhatsApp Watcher",
      "status": "healthy",
      "last_check": "2026-02-24T10:30:00Z",
      "last_error": null,
      "consecutive_failures": 0
    }
  },
  "updated_at": "2026-02-24T10:30:00Z"
}
```

### Status Values

| Status | Meaning | Trigger |
|--------|---------|---------|
| `healthy` | Component working normally | Successful operation |
| `degraded` | Intermittent failures | 1-2 consecutive failures |
| `down` | Component unavailable | 3+ consecutive failures |
| `unknown` | Not yet checked | System startup |

---

## 8. Extended Approval File (Gold)

### New action_type Values

| action_type | Platform | Requires |
|-------------|----------|----------|
| `facebook_post` | Facebook | page_id, message |
| `facebook_reply` | Facebook | post_id, comment_id, message |
| `instagram_post` | Instagram | ig_user_id, caption, image_url |
| `instagram_reel` | Instagram | ig_user_id, caption, video_url |
| `instagram_reply` | Instagram | comment_id, reply_message |
| `odoo_payment` | Odoo | invoice_id, amount |

---

## 9. Extended Dashboard (Gold)

### New Sections

```markdown
## Financial Summary (Odoo)

| Metric | Value |
|--------|-------|
| Revenue (This Week) | PKR {{ODOO_REVENUE}} |
| Pending Invoices | {{ODOO_PENDING_INVOICES}} |
| Recent Expenses | PKR {{ODOO_EXPENSES}} |

## Social Media

| Platform | Posts | Engagement | Last Post |
|----------|-------|------------|-----------|
| Facebook | {{FB_POST_COUNT}} | {{FB_ENGAGEMENT}} | {{FB_LAST_POST}} |
| Instagram | {{IG_POST_COUNT}} | {{IG_ENGAGEMENT}} | {{IG_LAST_POST}} |

## System Health

| Component | Status | Last Check |
|-----------|--------|------------|
| Odoo | {{ODOO_STATUS}} | {{ODOO_LAST_CHECK}} |
| Facebook | {{FB_STATUS}} | {{FB_LAST_CHECK}} |
| Instagram | {{IG_STATUS}} | {{IG_LAST_CHECK}} |
| Gmail | {{GMAIL_STATUS}} | {{GMAIL_LAST_CHECK}} |
| WhatsApp | {{WA_STATUS}} | {{WA_LAST_CHECK}} |
```

---

## Data Integrity Rules (Gold Extensions)

1. **Workflow consistency**: All actions in a workflow MUST share the same `workflow_id`
2. **Approval before external**: No Facebook/Instagram/Odoo payment action executes without approval
3. **Audit completeness**: Every MCP tool call MUST produce a log entry
4. **Health accuracy**: Component health MUST be updated after every operation
5. **Briefing completeness**: CEO Briefing MUST note missing data sources, never silently omit
6. **Log sanitization**: Audit logs MUST never contain tokens, passwords, or full credit card numbers
7. **Ralph Wiggum bounds**: Task files MUST have max_iterations set; loop MUST respect it
