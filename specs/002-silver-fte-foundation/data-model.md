# Data Model: Silver Tier — Functional Assistant

**Feature**: 002-silver-fte-foundation
**Date**: 2026-02-18
**Source**: [spec.md](./spec.md)
**Extends**: [Bronze data-model.md](../001-bronze-fte-foundation/data-model.md)

---

## Entity Overview

| Entity | Storage | Format | Location | New in Silver |
|--------|---------|--------|----------|---------------|
| Action File | Markdown | YAML frontmatter + body | Needs_Action/, Done/ | Extended |
| Email Action | Markdown | YAML frontmatter + body | Needs_Action/ | ✅ New |
| WhatsApp Action | Markdown | YAML frontmatter + body | Needs_Action/ | ✅ New |
| Approval File | Markdown | YAML frontmatter + body | Pending_Approval/, Approved/, Rejected/ | Extended |
| Plan.md | Markdown | Checkboxes + notes | Plans/ | ✅ New |
| Log Entry | JSON | JSON object in array | Logs/YYYY-MM-DD.json | Extended |
| Dashboard | Markdown | Template with placeholders | Dashboard.md | Extended |
| Agent Skill | Markdown | Structured procedure | .claude/skills/*.md | Extended |
| Schedule Config | JSON | Job definitions | schedules.json | ✅ New |
| Watcher Status | JSON | Runtime state | .state/watchers.json | ✅ New |

---

## 1. Email Action File

**Purpose**: Represents an incoming email requiring AI processing.

**Lifecycle**: Gmail Watcher detects email → Creates in `Needs_Action/` → Claude processes → `Done/`

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Always `email` | `email` |
| message_id | string | Yes | Gmail message ID | `18d4a5b2c3e4f5g6` |
| thread_id | string | Yes | Gmail thread ID | `18d4a5b2c3e4f5g6` |
| from | string | Yes | Sender email | `client@example.com` |
| from_name | string | No | Sender display name | `John Client` |
| to | string | Yes | Recipient email | `owner@example.com` |
| subject | string | Yes | Email subject | `Re: Invoice Question` |
| date | datetime | Yes | Email timestamp | `2026-02-18T10:30:00Z` |
| labels | array | No | Gmail labels | `['IMPORTANT', 'UNREAD']` |
| snippet | string | Yes | First 100 chars of body | `Hi, I wanted to ask about...` |
| status | enum | Yes | `pending`, `processing`, `completed` | `pending` |
| detected_at | datetime | Yes | When watcher found it | `2026-02-18T10:31:00Z` |
| has_attachments | boolean | No | Whether email has attachments | `true` |
| attachment_names | array | No | List of attachment filenames | `['invoice.pdf']` |

### File Naming Convention

```
EMAIL_{message_id}.md
```

Example: `EMAIL_18d4a5b2c3e4f5g6.md`

### Body Content

```markdown
---
type: email
message_id: 18d4a5b2c3e4f5g6
from: client@example.com
subject: Re: Invoice Question
date: 2026-02-18T10:30:00Z
status: pending
---

## Email Content

Hi,

I wanted to ask about the invoice you sent last week...

## Suggested Actions

- [ ] Draft reply
- [ ] Forward to relevant team
- [ ] Archive (no action needed)

## Context

Thread contains 3 previous messages.
```

---

## 2. WhatsApp Action File

**Purpose**: Represents a WhatsApp message requiring AI processing.

**Lifecycle**: WhatsApp Watcher detects message → Creates in `Needs_Action/` → Claude processes → `Done/`

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Always `whatsapp` | `whatsapp` |
| sender | string | Yes | Sender name/number | `+1234567890` |
| sender_name | string | No | Contact name if available | `John Client` |
| chat_type | enum | Yes | `individual`, `group` | `individual` |
| group_name | string | No | Group name if chat_type=group | `Project Team` |
| message | string | Yes | Full message text | `Urgent: Need invoice ASAP` |
| timestamp | datetime | Yes | Message timestamp | `2026-02-18T10:30:00Z` |
| detected_at | datetime | Yes | When watcher found it | `2026-02-18T10:31:00Z` |
| keywords_matched | array | Yes | Which keywords triggered | `['urgent', 'invoice']` |
| status | enum | Yes | `pending`, `processing`, `completed` | `pending` |
| has_media | boolean | No | Whether message has media | `false` |

### File Naming Convention

```
WA_{sender_sanitized}_{timestamp_compact}.md
```

Example: `WA_1234567890_20260218T103000Z.md`

### Validation Rules

1. `keywords_matched` MUST contain at least one keyword
2. `sender` MUST NOT be empty
3. `message` MUST NOT be empty

---

## 3. Plan.md (Reasoning Scratchpad)

**Purpose**: Claude's reasoning artifact for complex multi-step tasks.

**Lifecycle**: Complex task detected → Plan created → Steps executed → Plan marked complete

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Always `plan` | `plan` |
| task | string | Yes | Task description | `Research competitor and draft outreach` |
| created_at | datetime | Yes | When plan created | `2026-02-18T10:30:00Z` |
| status | enum | Yes | `in_progress`, `completed`, `blocked` | `in_progress` |
| source_file | string | No | Action file that triggered this | `Needs_Action/EMAIL_123.md` |
| steps_total | integer | Yes | Total number of steps | `5` |
| steps_completed | integer | Yes | Completed steps count | `2` |
| requires_approval | boolean | Yes | Whether any step needs HITL | `true` |
| updated_at | datetime | Yes | Last modification time | `2026-02-18T10:45:00Z` |

### File Naming Convention

```
PLAN_{task_slug}_{YYYY-MM-DD}.md
```

Example: `PLAN_competitor_research_2026-02-18.md`

### Body Structure

```markdown
---
type: plan
task: Research competitor X and draft outreach email
created_at: 2026-02-18T10:30:00Z
status: in_progress
steps_total: 5
steps_completed: 2
requires_approval: true
---

# Plan: Research Competitor X

## Steps

- [x] Identify competitor's main products (completed 10:32)
- [x] Review their LinkedIn presence (completed 10:35)
- [ ] Draft outreach email content
- [ ] Create approval request for email (REQUIRES APPROVAL)
- [ ] Send email via MCP

## Notes

Found that Competitor X focuses on enterprise clients.
Their LinkedIn posts 3x weekly, mostly case studies.

## Blockers

None currently.
```

### Step Format

```
- [ ] Step description
- [x] Step description (completed HH:MM)
- [ ] Step description (REQUIRES APPROVAL)
- [ ] Step description (BLOCKED: reason)
```

---

## 4. Extended Approval File

**Purpose**: Extended from Bronze to support email and LinkedIn actions.

### New action_type Values (Silver)

| action_type | Platform | Requires |
|-------------|----------|----------|
| `send_email` | Gmail | to, subject, body |
| `linkedin_post` | LinkedIn | content, visibility |
| `whatsapp_reply` | WhatsApp | to, message |

### Details Object Extensions

**send_email**:
```yaml
details:
  to: "client@example.com"
  cc: "team@company.com"  # optional
  subject: "Re: Invoice Question"
  body: |
    Hi John,

    Thank you for your question...
  body_preview: "Hi John, Thank you for..."
  attachments: []
  reply_to_message_id: "18d4a5b2c3e4f5g6"  # if replying
```

**linkedin_post**:
```yaml
details:
  content: |
    Excited to announce our new product launch!

    #innovation #business
  visibility: "public"  # public | connections
  has_image: false
  image_path: null
```

**whatsapp_reply**:
```yaml
details:
  to: "+1234567890"
  chat_name: "John Client"
  message: "Thanks for reaching out! I'll send the invoice today."
  reply_to_message: "Urgent: Need invoice ASAP"
```

---

## 5. Schedule Configuration

**Purpose**: Defines scheduled tasks for APScheduler.

**Location**: `config/schedules.json`

### Schema

```json
{
  "schedules": [
    {
      "id": "gmail_check",
      "task": "check_gmail",
      "cron": "0 9 * * *",
      "enabled": true,
      "description": "Check Gmail every day at 9 AM"
    },
    {
      "id": "whatsapp_check",
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
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier |
| task | string | Yes | Task function name |
| cron | string | No | Cron expression (mutually exclusive with interval) |
| interval_minutes | integer | No | Minutes between runs |
| enabled | boolean | Yes | Whether schedule is active |
| description | string | Yes | Human-readable description |

---

## 6. Watcher Status

**Purpose**: Runtime state of all watchers for Dashboard display.

**Location**: `.state/watchers.json`

### Schema

```json
{
  "watchers": {
    "gmail": {
      "name": "Gmail Watcher",
      "status": "running",
      "last_check": "2026-02-18T10:30:00Z",
      "last_result": "success",
      "items_today": 5,
      "errors_today": 0,
      "started_at": "2026-02-18T08:00:00Z"
    },
    "whatsapp": {
      "name": "WhatsApp Watcher",
      "status": "running",
      "last_check": "2026-02-18T10:29:00Z",
      "last_result": "success",
      "items_today": 3,
      "errors_today": 0,
      "session_valid": true,
      "started_at": "2026-02-18T08:00:00Z"
    },
    "inbox": {
      "name": "Inbox Watcher",
      "status": "running",
      "last_check": "2026-02-18T10:30:00Z",
      "last_result": "success",
      "items_today": 2,
      "errors_today": 0,
      "started_at": "2026-02-18T08:00:00Z"
    }
  },
  "updated_at": "2026-02-18T10:30:00Z"
}
```

### Status Values

| Status | Meaning |
|--------|---------|
| `running` | Watcher is active and checking |
| `stopped` | Watcher is not running |
| `error` | Watcher encountered persistent error |
| `session_expired` | Session needs re-authentication |

---

## 7. Extended Dashboard

**Purpose**: Silver tier additions to Dashboard.md.

### New Placeholders

| Placeholder | Type | Description |
|-------------|------|-------------|
| `{{WATCHER_STATUS_TABLE}}` | markdown table | Status of all watchers |
| `{{PLATFORM_STATS_TABLE}}` | markdown table | Stats per platform |
| `{{GMAIL_COUNT}}` | integer | Emails processed today |
| `{{WHATSAPP_COUNT}}` | integer | WhatsApp messages today |
| `{{LINKEDIN_COUNT}}` | integer | LinkedIn posts today |
| `{{SCHEDULED_TASKS}}` | markdown list | Upcoming scheduled tasks |

### Extended Template

```markdown
# AI Employee Dashboard

**Last Updated**: {{LAST_UPDATED}}
**Status**: {{STATUS}}

## Watcher Status

{{WATCHER_STATUS_TABLE}}

## Current Stats

| Metric | Value |
|--------|-------|
| Pending Tasks | {{PENDING_COUNT}} |
| Awaiting Approval | {{APPROVAL_COUNT}} |
| Completed Today | {{COMPLETED_TODAY}} |

## Platform Stats

{{PLATFORM_STATS_TABLE}}

## Recent Activity

{{RECENT_ACTIVITY}}

## Pending Approvals

{{PENDING_APPROVALS}}

## Upcoming Scheduled Tasks

{{SCHEDULED_TASKS}}
```

---

## 8. Extended Log Entry

**Purpose**: Silver tier additions to log entries.

### New action_type Values

| action_type | Source | Description |
|-------------|--------|-------------|
| `email_detected` | Gmail Watcher | New email found |
| `email_processed` | Claude | Email action file created |
| `email_sent` | MCP Server | Email sent successfully |
| `whatsapp_detected` | WhatsApp Watcher | New message found |
| `whatsapp_processed` | Claude | WhatsApp action created |
| `linkedin_post_created` | Claude | Post content generated |
| `linkedin_post_published` | Playwright | Post published |
| `plan_created` | Claude | Plan.md created |
| `plan_step_completed` | Claude | Step marked complete |
| `schedule_triggered` | APScheduler | Scheduled task ran |
| `session_expired` | Watcher | Session needs refresh |

### Extended Fields

| Field | Type | Description |
|-------|------|-------------|
| platform | string | `email`, `whatsapp`, `linkedin`, `file` |
| message_id | string | Platform-specific ID |
| schedule_id | string | If triggered by scheduler |

---

## 9. Agent Skill (Silver Tier)

**Purpose**: Extended skills for Silver functionality.

### Silver Tier Skills

| Skill | Platform | Trigger |
|-------|----------|---------|
| email_responder.md | email | EMAIL_*.md in Needs_Action/ |
| whatsapp_handler.md | whatsapp | WA_*.md in Needs_Action/ |
| linkedin_poster.md | linkedin | Manual request or schedule |
| plan_creator.md | general | Complex task detection |
| approval_checker.md | general | File moved to Approved/ |

### Extended Skill Template

```markdown
# Skill: [Name]

## Purpose
[Description]

## Platform
email | whatsapp | linkedin | general

## Trigger
[What causes this skill to be invoked]

## Inputs
- [input_1]: [description]

## Steps
1. [Step]

## Approval Required
[Specify conditions requiring HITL approval]

## Output
- Files created: [list]
- Files modified: [list]
- External actions: [list]

## Logging
[What to log]

## Error Handling
[How to handle failures]
```

---

## State Transitions

### Email Action Lifecycle

```
[Gmail Watcher detects email]
         ↓
   EMAIL_*.md created in Needs_Action/
         ↓
   Claude reads + processes
         ↓
   ┌─────┴─────┐
   ↓           ↓
Reply needed  No action
   ↓           ↓
Approval      Done/
request
   ↓
Approved → MCP sends email → Done/
```

### WhatsApp Action Lifecycle

```
[WhatsApp Watcher detects keyword message]
         ↓
   WA_*.md created in Needs_Action/
         ↓
   Claude reads + processes
         ↓
   ┌─────┴─────┐
   ↓           ↓
Reply needed  Log only
   ↓           ↓
Approval      Done/
request
   ↓
Approved → WhatsApp reply → Done/
```

### Plan.md Lifecycle

```
[Complex task detected]
         ↓
   Plan.md created in Plans/
         ↓
   Execute steps sequentially
         ↓
   ┌─────┴─────┐
   ↓           ↓
Step needs    Step auto
approval      executable
   ↓           ↓
Wait for      Mark [x]
approval      continue
   ↓
All steps complete → status: completed
```

---

## Data Integrity Rules (Extended)

1. **Platform consistency**: Action files MUST have correct type for their prefix
2. **Plan coherence**: steps_completed MUST match actual [x] count
3. **Schedule uniqueness**: schedule IDs MUST be unique
4. **Watcher state**: Status JSON MUST be updated on every check
5. **Cross-reference**: approval files MUST reference valid source files
