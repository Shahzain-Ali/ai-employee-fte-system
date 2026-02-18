# Data Model: Bronze Tier — Personal AI Employee Foundation

**Feature**: 001-bronze-fte-foundation
**Date**: 2026-02-17
**Source**: [spec.md](./spec.md)

---

## Entity Overview

| Entity | Storage | Format | Location |
|--------|---------|--------|----------|
| Action File | Markdown | YAML frontmatter + body | Needs_Action/, Done/ |
| Approval File | Markdown | YAML frontmatter + body | Pending_Approval/, Approved/, Rejected/ |
| Log Entry | JSON | JSON object in array | Logs/YYYY-MM-DD.json |
| Dashboard | Markdown | Template with placeholders | Dashboard.md |
| Handbook | Markdown | Rules document | Company_Handbook.md |
| Agent Skill | Markdown | Structured procedure | .claude/skills/*.md |

---

## 1. Action File

**Purpose**: Represents one unit of work for the AI Employee to process.

**Lifecycle**: Created in `Needs_Action/` → Processed → Moved to `Done/`

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Action category | `file_drop`, `manual_task` |
| original_name | string | Yes | Original filename (for file drops) | `invoice_january.pdf` |
| file_size | integer | No | Size in bytes | `102400` |
| file_type | string | Yes | MIME type or extension | `application/pdf`, `.pdf` |
| detected_at | datetime | Yes | ISO 8601 timestamp | `2026-02-17T10:30:00Z` |
| status | enum | Yes | `pending`, `processing`, `completed`, `failed` | `pending` |
| priority | enum | No | `low`, `normal`, `high` | `normal` |
| source | string | Yes | Where the action originated | `Inbox/`, `manual` |
| processed_at | datetime | No | When processing completed | `2026-02-17T10:32:00Z` |
| error_message | string | No | If status is `failed` | `Timeout exceeded` |

### File Naming Convention

```
FILE_<original_name_sanitized>.md
```

- Sanitized: spaces → underscores, special chars removed
- Example: `FILE_invoice_january.pdf.md`

### Validation Rules

1. `type` MUST be one of: `file_drop`, `manual_task`, `rejected_file`
2. `detected_at` MUST be valid ISO 8601 datetime
3. `status` MUST start as `pending` when created
4. `file_size` MUST be non-negative integer if present
5. `original_name` MUST NOT contain path separators

---

## 2. Approval File

**Purpose**: Represents a sensitive action requiring human approval before execution.

**Lifecycle**: Created in `Pending_Approval/` → Owner moves to `Approved/` or `Rejected/` → Processed

### Fields (YAML Frontmatter)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Always `approval_request` | `approval_request` |
| action_type | string | Yes | What action needs approval | `payment`, `email_send`, `file_delete` |
| source_file | string | Yes | Original action file path | `Needs_Action/FILE_invoice.md` |
| created_at | datetime | Yes | When approval requested | `2026-02-17T10:30:00Z` |
| reason | string | Yes | Why approval is needed | `Payment exceeds $100 threshold` |
| details | object | Yes | Action-specific details | See below |
| approved_at | datetime | No | When approved (set by system) | `2026-02-17T10:35:00Z` |
| rejected_at | datetime | No | When rejected (set by system) | `2026-02-17T10:35:00Z` |
| decision_by | string | No | Who made decision | `owner` |

### Details Object (by action_type)

**payment**:
```yaml
details:
  amount: 150.00
  currency: USD
  recipient: "Vendor Name"
  description: "Invoice payment"
```

**email_send**:
```yaml
details:
  to: "unknown@example.com"
  subject: "Re: Your inquiry"
  body_preview: "First 100 characters..."
```

**file_delete**:
```yaml
details:
  file_path: "/path/to/file.pdf"
  file_size: 102400
  reason: "Duplicate detected"
```

### File Naming Convention

```
APPROVAL_<action_type>_<timestamp>.md
```

- Example: `APPROVAL_payment_20260217T103000Z.md`

### Validation Rules

1. `action_type` MUST be one of: `payment`, `email_send`, `file_delete`
2. `source_file` MUST reference existing file in Needs_Action/
3. `details` MUST contain required fields for the action_type
4. File can only exist in ONE location at a time

---

## 3. Log Entry

**Purpose**: Audit trail of all AI Employee actions for accountability.

**Storage**: JSON array in `Logs/YYYY-MM-DD.json`

### Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | string | Yes | Unique identifier (UUID v4) | `550e8400-e29b-41d4-a716-446655440000` |
| timestamp | datetime | Yes | ISO 8601 when action occurred | `2026-02-17T10:30:00Z` |
| action_type | string | Yes | What was done | `file_detected`, `processing_started`, `task_completed` |
| source | string | Yes | What triggered the action | `filesystem_watcher`, `orchestrator`, `claude_code` |
| target_file | string | No | File being acted upon | `Needs_Action/FILE_invoice.md` |
| status | string | Yes | Result of action | `success`, `failure`, `pending_approval` |
| details | object | No | Additional context | `{"skill_used": "process_document"}` |
| approval_status | string | No | For HITL actions | `not_required`, `pending`, `approved`, `rejected` |
| duration_ms | integer | No | How long action took | `1500` |
| error | string | No | Error message if failed | `Claude Code timeout` |

### Action Types

| action_type | Triggered By | Description |
|-------------|--------------|-------------|
| `file_detected` | Watcher | New file found in Inbox/ |
| `action_file_created` | Watcher | Created .md in Needs_Action/ |
| `processing_started` | Orchestrator | Claude Code triggered |
| `processing_completed` | Claude Code | Task finished successfully |
| `processing_failed` | Claude Code | Task failed with error |
| `approval_requested` | Claude Code | Sensitive action detected |
| `approval_granted` | Orchestrator | Owner approved action |
| `approval_denied` | Orchestrator | Owner rejected action |
| `file_moved` | System | File moved between folders |
| `dashboard_updated` | Claude Code | Dashboard.md refreshed |

### Validation Rules

1. `id` MUST be unique within the log file
2. `timestamp` MUST be valid ISO 8601
3. `action_type` MUST be from defined list
4. Log file MUST be valid JSON array
5. New entries MUST be appended, never overwrite existing

---

## 4. Dashboard

**Purpose**: Real-time status view for the owner.

**Location**: `AI_Employee_Vault/Dashboard.md`

### Template Structure

```markdown
# AI Employee Dashboard

**Last Updated**: {{LAST_UPDATED}}
**Status**: {{STATUS}}

## Current Stats

| Metric | Value |
|--------|-------|
| Pending Tasks | {{PENDING_COUNT}} |
| Awaiting Approval | {{APPROVAL_COUNT}} |
| Completed Today | {{COMPLETED_TODAY}} |

## Recent Activity

{{RECENT_ACTIVITY}}

## Pending Approvals

{{PENDING_APPROVALS}}
```

### Placeholder Definitions

| Placeholder | Type | Update Frequency |
|-------------|------|------------------|
| `{{LAST_UPDATED}}` | datetime | Every update |
| `{{STATUS}}` | enum: Idle, Working, Waiting for Approval | Real-time |
| `{{PENDING_COUNT}}` | integer | When Needs_Action/ changes |
| `{{APPROVAL_COUNT}}` | integer | When Pending_Approval/ changes |
| `{{COMPLETED_TODAY}}` | integer | When Done/ changes |
| `{{RECENT_ACTIVITY}}` | markdown list | Last 5 log entries |
| `{{PENDING_APPROVALS}}` | markdown list | Links to Pending_Approval/ files |

---

## 5. Handbook

**Purpose**: The AI Employee's rulebook defining behavior and constraints.

**Location**: `AI_Employee_Vault/Company_Handbook.md`

### Required Sections

1. **Identity**: Agent name, role, owner info
2. **Working Hours**: When the agent is active
3. **Approval Thresholds**: What actions require HITL
4. **Forbidden Actions**: What the agent must never do
5. **Response Guidelines**: Tone, format, communication style
6. **Escalation Rules**: When to alert the owner

### Approval Thresholds (Bronze Tier)

| Action Category | Threshold | Requires Approval |
|-----------------|-----------|-------------------|
| Payments | Any amount | Always |
| Emails | To unknown contacts | Always |
| File Deletions | Any file | Always |
| File Processing | Standard docs | Never |
| Dashboard Updates | Any | Never |

---

## 6. Agent Skill

**Purpose**: Reusable AI procedure that defines how to handle specific tasks.

**Location**: `.claude/skills/<skill_name>.md`

### Required Sections

```markdown
# Skill: <Skill Name>

## Purpose
<One sentence describing what this skill does>

## Inputs
- <input_1>: <description>
- <input_2>: <description>

## Steps
1. <First step>
2. <Second step>
3. ...

## Output
<What this skill produces>

## Logging
<What to log for audit trail>

## Error Handling
<How to handle failures>
```

### Bronze Tier Skills

| Skill Name | Purpose | Inputs |
|------------|---------|--------|
| process_document | Generic document handling | Action file path |
| update_dashboard | Refresh Dashboard.md stats | None (reads vault state) |
| create_approval_request | Generate HITL approval file | Action details, reason |

---

## State Transitions

### Action File Lifecycle

```
[Created] → pending → processing → completed → [Moved to Done/]
                   ↘            ↘
                    failed       pending_approval → approved → completed
                                                 ↘
                                                  rejected → [Logged & closed]
```

### Approval File Lifecycle

```
[Created in Pending_Approval/]
         ↓
   Owner reviews
         ↓
   ┌─────┴─────┐
   ↓           ↓
Approved/   Rejected/
   ↓           ↓
Action      Log entry
executed    created
   ↓           ↓
Done/       Done/
```

---

## Indexes & Queries

### Common Queries (via file system)

| Query | Implementation |
|-------|----------------|
| Pending tasks | `ls Needs_Action/*.md` |
| Awaiting approval | `ls Pending_Approval/*.md` |
| Today's completed | `ls Done/*.md` filtered by date |
| Logs for date | `cat Logs/YYYY-MM-DD.json` |
| Failed actions | `grep "status.*failed" Logs/*.json` |

---

## Data Integrity Rules

1. **No orphan files**: Every action file MUST have corresponding log entries
2. **Single location**: A file can only exist in ONE folder at a time
3. **Immutable logs**: Log entries are append-only, never modified or deleted
4. **Atomic moves**: File moves must be atomic to prevent partial states
5. **Timestamp ordering**: Log entries must be in chronological order
