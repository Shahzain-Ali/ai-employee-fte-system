# Feature Specification: Hackathon-0 Silver Tier — Functional Assistant

**Feature Branch**: `002-silver-fte-foundation`
**Created**: 2026-02-18
**Status**: Draft
**Input**: Silver Tier: Functional Assistant — Extends Bronze tier with multiple watchers
(Gmail, WhatsApp, LinkedIn), Claude reasoning loop with Plan.md, working MCP server,
human-in-the-loop approval workflow, basic scheduling, and all AI as Agent Skills.

---

## Official Requirements (Hackathon Documentation Page 4)

**Silver Tier: Functional Assistant** — Estimated time: 20-30 hours

1. All Bronze requirements plus:
2. Two or more Watcher scripts (e.g., Gmail + WhatsApp + LinkedIn)
3. Automatically Post on LinkedIn about business to generate sales
4. Claude reasoning loop that creates Plan.md files
5. One working MCP server for external action (e.g., sending emails)
6. Human-in-the-loop approval workflow for sensitive actions
7. Basic scheduling via cron or Task Scheduler
8. All AI functionality should be implemented as Agent Skills

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Gmail Watcher Detects Emails (Priority: P1)

The owner connects their Gmail account via OAuth2. When important unread emails
arrive, the Gmail Watcher automatically detects them and creates action files
in Needs_Action/ for Claude to process. This enables autonomous email triage
without manual inbox checking.

**Why this priority**: Email is the most critical business communication channel.
Detecting incoming emails is the foundation for automated email workflows.

**Independent Test**: Send a test email marked as important. Within 2 minutes,
an EMAIL_{message_id}.md file appears in Needs_Action/ with sender, subject,
and body content.

**Acceptance Scenarios**:

1. **Given** the Gmail Watcher is running with valid OAuth2 credentials, **When**
   an important unread email arrives, **Then** within 2 minutes an EMAIL_{id}.md
   file is created in Needs_Action/ containing sender, subject, timestamp, and body.

2. **Given** credentials.json exists with valid OAuth2 tokens, **When** the Gmail
   Watcher starts, **Then** it authenticates with Gmail API and begins polling for
   unread important emails.

3. **Given** the Gmail Watcher creates an action file, **When** Claude processes it,
   **Then** the email is marked as read in Gmail (or flagged as processed).

4. **Given** OAuth2 tokens expire, **When** the watcher attempts to poll, **Then**
   it automatically refreshes tokens without requiring manual re-authentication.

---

### User Story 2 — Human-in-the-Loop Approval Workflow (Priority: P2)

For sensitive actions (sending emails, LinkedIn posts, payments), the system
creates an approval request file in Pending_Approval/. The owner reviews these
files in Obsidian and moves them to Approved/ to proceed or Rejected/ to cancel.
No sensitive action ever executes without explicit human consent.

**Why this priority**: Human approval is the core safety mechanism. Without it,
the AI cannot be trusted to perform external actions autonomously.

**Independent Test**: Trigger a sensitive action (e.g., email reply). Verify a
file appears in Pending_Approval/. Move it to Approved/. Verify the action executes.

**Acceptance Scenarios**:

1. **Given** Claude determines an action requires approval, **When** it creates the
   approval request, **Then** a file named ACTION_{type}_{id}_{date}.md appears in
   Pending_Approval/ with action details, amount (if applicable), and clear instructions.

2. **Given** an approval file exists in Pending_Approval/, **When** the owner moves
   it to Approved/, **Then** the orchestrator detects this within 60 seconds and
   executes the approved action.

3. **Given** an approval file exists in Pending_Approval/, **When** the owner moves
   it to Rejected/, **Then** the action is canceled and logged as rejected.

4. **Given** an approval file sits in Pending_Approval/ for 24 hours without action,
   **Then** the system logs a reminder but takes no automatic action.

---

### User Story 3 — WhatsApp Watcher via Playwright (Priority: P3)

The owner sets up WhatsApp Web monitoring using Playwright with persistent browser
sessions. When messages containing configured keywords (urgent, payment, invoice, etc.)
arrive, the watcher creates action files for Claude to process.

**Why this priority**: WhatsApp is the second most critical communication channel
for many businesses. Playwright enables free monitoring without Twilio costs.

**Independent Test**: Send a WhatsApp message containing "urgent". Within 2 minutes,
a WA_{sender}_{timestamp}.md file appears in Needs_Action/.

**Acceptance Scenarios**:

1. **Given** the WhatsApp Watcher is running with a logged-in session, **When** a
   message containing a configured keyword arrives, **Then** a WA_{sender}_{ts}.md
   file is created in Needs_Action/ with sender, message content, and timestamp.

2. **Given** Playwright is configured with persistent context, **When** the watcher
   restarts, **Then** it resumes the existing WhatsApp Web session without requiring
   QR code re-scan.

3. **Given** a message arrives without any configured keywords, **When** the watcher
   checks it, **Then** no action file is created (normal messages are ignored).

4. **Given** WhatsApp Web requires re-authentication, **When** the watcher detects
   this, **Then** it creates a notification file requesting owner to re-scan QR code.

---

### User Story 4 — Claude Reasoning Loop Creates Plan.md (Priority: P4)

For complex multi-step tasks, Claude creates a Plan.md file with checkboxes for
each step. This provides transparency into the AI's reasoning and allows the owner
to review and approve multi-step workflows before execution.

**Why this priority**: Plan.md makes AI reasoning explicit and reviewable. It enables
human oversight of complex task decomposition.

**Independent Test**: Request a complex task (e.g., "research competitor X and draft
outreach email"). Verify Plan.md is created with logical steps and checkboxes.

**Acceptance Scenarios**:

1. **Given** Claude receives a complex multi-step task, **When** it begins planning,
   **Then** it creates a PLAN_{task_slug}_{date}.md file in Plans/ with markdown
   checkboxes for each step.

2. **Given** a Plan.md exists with unchecked steps, **When** Claude completes a step,
   **Then** the corresponding checkbox is marked with [x] and a completion timestamp.

3. **Given** a step in Plan.md requires human approval, **When** Claude reaches that
   step, **Then** it pauses execution and creates an approval file before proceeding.

4. **Given** the owner modifies Plan.md (adds/removes steps), **When** Claude resumes
   processing, **Then** it follows the updated plan.

---

### User Story 5 — Email MCP Server Sends Emails (Priority: P5)

A working MCP server enables Claude to send emails via Gmail API. The server
exposes send_email with to, subject, body, and optional attachment parameters.
All email sends require prior human approval.

**Why this priority**: Email sending is the most valuable external action capability.
MCP standardizes how Claude interacts with external services.

**Independent Test**: Approve an email action. Verify the email is sent via MCP
and received by the recipient.

**Acceptance Scenarios**:

1. **Given** the email MCP server is configured in claude-code/mcp.json, **When**
   Claude Code starts, **Then** it successfully connects to the email MCP server.

2. **Given** an approved email action exists, **When** Claude invokes send_email
   via MCP, **Then** the email is sent to the specified recipient with correct
   subject and body.

3. **Given** the MCP server fails to send (network error, auth failure), **When**
   Claude attempts to send, **Then** the error is logged and the action is retried
   up to 3 times before marking as failed.

4. **Given** an email send succeeds, **When** the MCP returns confirmation, **Then**
   a log entry is created with message_id, recipient, and timestamp.

---

### User Story 6 — LinkedIn Auto-Post via Playwright (Priority: P6)

The owner can request LinkedIn posts about their business. Claude drafts the post
content, creates an approval file, and upon approval, Playwright automates posting
to LinkedIn. This generates sales leads without manual social media management.

**Why this priority**: LinkedIn posting drives business development. Automation
saves time while human approval ensures quality control.

**Independent Test**: Request a LinkedIn post. Verify approval file is created.
Approve it. Verify post appears on LinkedIn (sandbox/test mode acceptable).

**Acceptance Scenarios**:

1. **Given** the owner requests a LinkedIn post, **When** Claude drafts content,
   **Then** an approval file is created in Pending_Approval/ with the post text
   and a preview of how it will appear.

2. **Given** a LinkedIn post is approved, **When** Playwright executes the post,
   **Then** it navigates to LinkedIn, logs in (if needed), and creates the post.

3. **Given** Playwright encounters bot detection or CAPTCHA, **When** the post
   fails, **Then** a notification is created requesting manual intervention.

4. **Given** a LinkedIn post succeeds, **When** Playwright confirms, **Then** a
   log entry records the post URL, timestamp, and content summary.

---

### User Story 7 — Basic Scheduling via Cron/APScheduler (Priority: P7)

The owner can schedule recurring tasks (daily email checks, weekly LinkedIn posts)
using cron-style scheduling. Scheduled tasks run automatically at configured times
without manual triggering.

**Why this priority**: Scheduling enables true autonomy — the AI Employee works
on a predictable schedule without requiring manual intervention.

**Independent Test**: Schedule a task for 5 minutes from now. Verify it executes
at the scheduled time.

**Acceptance Scenarios**:

1. **Given** a task is configured with a cron expression, **When** the scheduled
   time arrives, **Then** the orchestrator triggers the task automatically.

2. **Given** APScheduler is running, **When** the system restarts, **Then**
   scheduled jobs are restored from persistence and continue running.

3. **Given** a scheduled task fails, **When** the scheduler logs the failure,
   **Then** it does not block subsequent scheduled executions.

4. **Given** the owner adds/removes scheduled tasks, **When** they update the
   schedule configuration, **Then** changes take effect within 60 seconds.

---

### User Story 8 — Enhanced Dashboard with Watcher Status (Priority: P8)

Dashboard.md displays the status of all watchers (running/stopped, last check time),
pending approvals count, and per-platform statistics (emails processed, WhatsApp
messages handled, LinkedIn posts made).

**Why this priority**: Visibility into system health enables the owner to quickly
identify issues and monitor the AI Employee's activity.

**Independent Test**: Open Dashboard.md. Verify it shows accurate watcher status
and counts that match actual system state.

**Acceptance Scenarios**:

1. **Given** watchers are running, **When** Dashboard.md is refreshed, **Then**
   it shows each watcher's status (Running/Stopped) and last check timestamp.

2. **Given** approval files exist in Pending_Approval/, **When** Dashboard.md
   is refreshed, **Then** the pending approvals count matches the actual file count.

3. **Given** actions have been processed, **When** Dashboard.md is refreshed,
   **Then** platform-specific stats show accurate totals (emails: X, WhatsApp: Y).

4. **Given** a watcher crashes, **When** Dashboard.md is refreshed, **Then** it
   shows that watcher as "Stopped" with the crash timestamp.

---

### Edge Cases

- What happens when Gmail OAuth2 credentials are revoked?
  The watcher creates a CREDENTIAL_ERROR.md in Needs_Action/ and halts polling
  until credentials are restored.

- What happens when WhatsApp Web session expires?
  The watcher creates a SESSION_EXPIRED.md notification requesting QR code re-scan.

- What happens when LinkedIn blocks the automation?
  The Playwright action fails, logs the error, and creates a notification for
  manual posting.

- What happens when two approval files for conflicting actions are both approved?
  Actions execute in order of approval timestamp; conflicting actions are logged.

- What happens when the MCP server is unavailable?
  Claude queues the action and retries every 5 minutes up to 3 times, then fails.

- What happens when Plan.md becomes corrupted or deleted mid-execution?
  Claude logs an error and creates a new Plan.md starting from the last completed step.

- What happens when scheduled tasks pile up (missed executions)?
  Missed tasks are logged but not retroactively executed; only future schedules run.

---

## Requirements *(mandatory)*

### Functional Requirements

**Gmail Watcher:**

- **FR-001**: Gmail Watcher MUST authenticate via Google OAuth2 credentials stored
  in credentials.json with automatic token refresh.

- **FR-002**: Gmail Watcher MUST query for unread important emails using Gmail API
  query: 'is:unread is:important'.

- **FR-003**: Gmail Watcher MUST create EMAIL_{message_id}.md action files in
  Needs_Action/ containing: sender, subject, timestamp, body (first 500 chars), labels.

- **FR-004**: Gmail Watcher MUST mark processed emails as read (or apply a custom
  label) to prevent duplicate processing.

**WhatsApp Watcher:**

- **FR-005**: WhatsApp Watcher MUST use Playwright with launch_persistent_context
  for session persistence across restarts.

- **FR-006**: WhatsApp Watcher MUST filter messages by configurable keyword list
  (default: urgent, asap, invoice, payment, help).

- **FR-007**: WhatsApp Watcher MUST create WA_{sender}_{timestamp}.md action files
  in Needs_Action/ containing: sender, message content, timestamp, chat context.

- **FR-008**: WhatsApp Watcher MUST detect session expiration and create notification
  files requesting QR code re-scan.

**MCP Email Server:**

- **FR-009**: MCP email server MUST expose send_email tool with parameters: to
  (required), subject (required), body (required), attachment (optional).

- **FR-010**: MCP email server MUST be configured in ~/.config/claude-code/mcp.json
  or project-level .mcp/config.json.

- **FR-011**: MCP email server MUST return confirmation with message_id upon
  successful send, or error details upon failure.

**LinkedIn Automation:**

- **FR-012**: LinkedIn Poster MUST use Playwright with stealth mode and random
  delays to minimize bot detection.

- **FR-013**: LinkedIn Poster MUST handle login flow (including 2FA wait) before
  attempting to post.

- **FR-014**: LinkedIn Poster MUST create posts with text content; image attachments
  are optional for Silver tier.

**Human-in-the-Loop:**

- **FR-015**: ALL external actions (email send, LinkedIn post, payments) MUST require
  human approval via file-based workflow.

- **FR-016**: Approval files MUST be created in Pending_Approval/ with clear
  instructions: "To Approve: Move to /Approved. To Reject: Move to /Rejected."

- **FR-017**: Orchestrator MUST watch Approved/ folder (polling every 60 seconds)
  and execute approved actions.

- **FR-018**: Rejected actions MUST be logged with rejection timestamp and reason
  (if provided in the file).

**Claude Reasoning Loop:**

- **FR-019**: Claude MUST create Plan.md for any task requiring 3+ steps, before
  executing any steps.

- **FR-020**: Plan.md files MUST be stored in Plans/ subfolder with naming:
  PLAN_{task_slug}_{YYYY-MM-DD}.md.

- **FR-021**: Each Plan.md step MUST be represented as a markdown checkbox:
  - [ ] Step description (pending) or - [x] Step description (completed).

- **FR-022**: Steps requiring approval MUST be marked with (REQUIRES APPROVAL) tag.

**Scheduling:**

- **FR-023**: Scheduler MUST support cron-style expressions for task timing.

- **FR-024**: Scheduler MUST persist job definitions to survive restarts.

- **FR-025**: Scheduler MUST log all scheduled task executions with timestamp
  and result (success/failure).

**Dashboard:**

- **FR-026**: Dashboard.md MUST show watcher status table: name, status
  (Running/Stopped), last check time, items processed today.

- **FR-027**: Dashboard.md MUST show pending approvals count with list of
  waiting items.

- **FR-028**: Dashboard.md MUST show platform stats: emails processed, WhatsApp
  messages handled, LinkedIn posts made, actions approved/rejected.

**Agent Skills:**

- **FR-029**: All AI logic MUST be implemented as Agent Skills in .claude/skills/.

- **FR-030**: Silver tier MUST add these skills: email_responder.md, whatsapp_handler.md,
  linkedin_poster.md, plan_creator.md, approval_checker.md.

---

### Key Entities

- **Email Action File**: Markdown file in Needs_Action/ (EMAIL_{id}.md) containing
  email metadata (sender, subject, timestamp, body preview) for AI processing.

- **WhatsApp Action File**: Markdown file in Needs_Action/ (WA_{sender}_{ts}.md)
  containing WhatsApp message details for AI processing.

- **Approval Request**: Markdown file in Pending_Approval/ (ACTION_{type}_{id}_{date}.md)
  representing a sensitive action awaiting human approval. Contains action details
  and clear move-to-approve/reject instructions.

- **Plan.md**: Markdown file in Plans/ (PLAN_{task}_{date}.md) containing Claude's
  reasoning scratchpad with checkbox steps for multi-step task execution.

- **MCP Server**: External process exposing tools (send_email, etc.) via MCP protocol.
  Configured in mcp.json with command, args, and environment variables.

- **Agent Skill (Silver)**: Markdown file in .claude/skills/ defining reusable AI
  procedure. Silver tier adds email, WhatsApp, LinkedIn, planning, and approval skills.

- **Schedule Configuration**: JSON or YAML file defining cron expressions and
  associated tasks for automated scheduling.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Gmail Watcher detects important unread emails and creates action files
  within 2 minutes — verified across 10 test emails.

- **SC-002**: WhatsApp Watcher detects keyword messages and creates action files
  within 2 minutes — verified with 5 keyword test messages.

- **SC-003**: No external action (email send, LinkedIn post) EVER executes without
  a corresponding approval file being moved to Approved/ — zero exceptions.

- **SC-004**: MCP email server successfully sends approved emails with correct
  content — verified by receiving test emails.

- **SC-005**: LinkedIn posts are published within 5 minutes of approval — verified
  with 3 test posts (can use test/sandbox mode).

- **SC-006**: Claude creates Plan.md with logical steps for complex tasks — verified
  by submitting 3 multi-step requests and reviewing plans.

- **SC-007**: Scheduled tasks execute within 60 seconds of their scheduled time —
  verified by scheduling 5 tasks and logging execution times.

- **SC-008**: Dashboard.md accurately reflects system state (watcher status, pending
  approvals, platform stats) within 2 minutes of changes.

- **SC-009**: All Silver tier Agent Skills exist in .claude/skills/ and are invoked
  correctly during appropriate workflows — verified by skill invocation logs.

- **SC-010**: The owner can easily understand Gmail, WhatsApp, and LinkedIn activity from
  the last 24 hours by reading Dashboard.md and Logs/ — no platform logins needed.

---

## Assumptions

- Bronze tier is fully implemented and functional before Silver tier begins.
- The owner has a Google Cloud project with Gmail API enabled and OAuth2 credentials.
- The owner has WhatsApp Web access and can perform initial QR code scan.
- The owner has a LinkedIn account for posting (personal or company page).
- Playwright is acceptable for browser automation (no commercial scraping restrictions).
- The owner's machine can run background processes (watchers, scheduler) continuously.
- MCP server implementation uses Node.js or Python; SDK documentation is available.
- Sensitive actions for Silver tier: email sends, LinkedIn posts, any external API calls.
- WhatsApp automation complies with owner's local terms of service understanding.

---

## Out of Scope (Silver Tier)

- Ralph Wiggum autonomous loop (Gold tier)
- Monday CEO Briefing generation (Gold tier)
- Odoo accounting integration (Gold tier)
- Facebook/Instagram/Twitter integration (Gold tier)
- Multi-agent coordination (Platinum tier)
- Cloud deployment or vault sync (Platinum tier)
- Payment processing beyond approval (requires Gold tier Odoo integration)
- Voice message transcription (future enhancement)
- Calendar integration and meeting scheduling (future enhancement)

---

## Technical Implementation Notes

### Gmail Watcher Implementation

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str):
        self.creds = Credentials.from_authorized_user_file(credentials_path)
        self.service = build('gmail', 'v1', credentials=self.creds)

    def check_for_updates(self):
        # Query: 'is:unread is:important'
        # Creates: EMAIL_{message_id}.md in Needs_Action/
```

### WhatsApp Watcher Implementation

```python
from playwright.sync_api import sync_playwright

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str, session_path: str):
        self.session_path = Path(session_path)
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help']

    def check_for_updates(self):
        # Uses launch_persistent_context for session persistence
        # Monitors WhatsApp Web for unread messages with keywords
```

### MCP Server Configuration

```json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["/path/to/email-mcp/index.js"],
      "env": { "GMAIL_CREDENTIALS": "/path/to/credentials.json" }
    }
  ]
}
```

### Human-in-the-Loop File Format

```markdown
# Pending_Approval/PAYMENT_Client_A_2026-01-07.md
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
status: pending
---
## To Approve: Move this file to /Approved folder.
## To Reject: Move this file to /Rejected folder.
```

---

## New Agent Skills

|         Skill         |                   Purpose                         |
|        -------        |                  ---------                        |
| email_responder.md    | Handle incoming emails, draft replies, categorize |
| whatsapp_handler.md   | Process WhatsApp messages, draft responses        |
| linkedin_poster.md    | Generate LinkedIn post content for approval       |
| plan_creator.md       | Create Plan.md for complex multi-step tasks       |
| approval_checker.md   | Check Approved/ folder and execute pending actions |

---

## Dependency Chain

```
Bronze Tier (complete)
    └── Silver Tier
        ├── Gmail Watcher (P1) ─────────┐
        ├── Human Approval (P2) ────────┼── Can be tested independently
        ├── WhatsApp Watcher (P3) ──────┤
        ├── Claude Reasoning Loop (P4) ─┤
        ├── Email MCP Server (P5) ──────┼── Requires Gmail + Approval
        ├── LinkedIn Poster (P6) ───────┼── Requires Approval
        ├── Scheduler (P7) ─────────────┤
        └── Enhanced Dashboard (P8) ────┘
```
