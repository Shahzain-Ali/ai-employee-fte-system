# Feature Specification: Hackathon-0 Gold Tier — Autonomous Employee

**Feature Branch**: `003-gold-fte-autonomous`
**Created**: 2026-02-23
**Status**: Draft
**Input**: Gold Tier: Autonomous Employee — Extends Silver tier with full cross-domain
integration (Personal + Business), Odoo accounting, Facebook/Instagram via Meta Graph API,
multiple MCP servers, CEO Briefing, error recovery, audit logging, Ralph Wiggum loop,
documentation, and all AI as Agent Skills. Optional: Twitter/X and personal Facebook via Playwright.

---

## Official Requirements (Hackathon Documentation Page 4)

**Gold Tier: Autonomous Employee** — Estimated time: 40+ hours

1. All Silver requirements plus:
2. Full cross-domain integration (Personal + Business)
3. Create an accounting system for your business in Odoo Community (self-hosted, local)
   and integrate it via an MCP server using Odoo's JSON-RPC APIs (Odoo 19+).
4. Integrate Facebook and Instagram and post messages and generate summary
5. Integrate Twitter (X) and post messages and generate summary
6. Multiple MCP servers for different action types
7. Weekly Business and Accounting Audit with CEO Briefing generation
8. Error recovery and graceful degradation
9. Comprehensive audit logging
10. Ralph Wiggum loop for autonomous multi-step task completion (see Section 2D)
11. Documentation of your architecture and lessons learned
12. All AI functionality should be implemented as Agent Skills

---

## Decisions & Context

### Decisions Made During Discussion (2026-02-23)

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Odoo Deployment | Docker (docker-compose) | Easy setup, isolated, easy cleanup |
| Facebook Integration | Meta Graph API via custom MCP server | Security & privacy — no third-party MCP servers |
| Instagram Integration | Meta Graph API via custom MCP server (convert personal account to Business or Creator) | Same security approach as Facebook; Creator account also supported since Instagram Platform API July 2024 |
| Twitter Integration | **OPTIONAL** — Playwright if time permits, Official API when budget available ($100/month) | Cost constraint — Twitter API Basic is $100/month |
| Personal Facebook Profile | **OPTIONAL** — Playwright if time permits | Meta Graph API only supports Pages, not personal profiles |
| Ralph Wiggum Completion | File-movement strategy | More reliable — task file moves to /Done when complete |
| MCP Server Approach | If Official MCP Servers available then use that and Not using any community-built MCP Servers instead Build all custom MCP servers (no third-party) | Security first — same approach as Silver tier email MCP |
| Meta Accounts | Need to create: Facebook Business Page (free), Instagram Business or Creator conversion (free), Meta Developer Account (free) | Pre-implementation setup required |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Odoo Accounting Integration (Priority: P1)

The owner sets up Odoo Community Edition via Docker on their local machine. The AI
Employee connects to Odoo via a custom MCP server using JSON-RPC API. When the AI
needs to create invoices, track payments, or generate financial reports, it communicates
with Odoo through this MCP server. This establishes the financial backbone for the
autonomous business employee.

**Why this priority**: Accounting is the foundation of the business domain. Without Odoo,
cross-domain integration, CEO Briefing, and weekly audits cannot function. Every other
Gold tier business feature depends on financial data from Odoo.

**Independent Test**: Start Odoo via docker-compose. Use the Odoo MCP server to create
an invoice for a test client. Verify the invoice appears in Odoo's web interface with
correct details (client name, amount, date).

**Acceptance Scenarios**:

1. **Given** Odoo is running via Docker with docker-compose, **When** the AI Employee
   invokes create_invoice via the Odoo MCP server, **Then** an invoice is created in
   Odoo with correct client name, amount, due date, and status "Draft".

2. **Given** an invoice exists in Odoo with status "Sent", **When** the AI Employee
   invokes mark_payment_received, **Then** the invoice status changes to "Paid" and
   the payment is recorded with timestamp.

3. **Given** Odoo is running, **When** the AI Employee invokes get_weekly_summary,
   **Then** it returns total revenue, total expenses, pending invoices count, and
   outstanding balance for the current week.

4. **Given** Docker is not running or Odoo is unreachable, **When** the AI Employee
   attempts any Odoo MCP call, **Then** the error is logged, the action is queued
   for retry, and the system continues operating without crashing.

---

### User Story 2 — Facebook Business Page Integration (Priority: P2)

The owner creates a Facebook Business Page and connects it via Meta Graph API through
a custom-built MCP server. The AI Employee can create posts on the Page, read comments,
reply to comments, and generate engagement summaries. All posting actions require human
approval before execution.

**Why this priority**: Facebook is the largest social media platform for business presence.
Page posting via official API is stable, free, and production-ready. It enables the
social media component of cross-domain integration.

**Independent Test**: Create a test post on the Facebook Business Page via the MCP server.
Verify the post appears on the Page. Generate a summary of recent posts and engagement.

**Acceptance Scenarios**:

1. **Given** the Facebook MCP server is configured with valid Meta Graph API credentials,
   **When** the AI Employee invokes create_page_post with a message, **Then** the post
   appears on the Facebook Business Page within 60 seconds.

2. **Given** posts exist on the Page, **When** the AI Employee invokes get_page_posts,
   **Then** it returns recent posts with content, timestamp, likes count, and comments count.

3. **Given** a post action is initiated, **When** the system creates an approval request,
   **Then** the post is NOT published until the owner moves the approval file to Approved/.

4. **Given** the Meta Graph API token expires, **When** the MCP server detects the error,
   **Then** it logs the failure, creates a notification file, and queues the action for retry
   after token refresh.

---

### User Story 3 — Instagram Business/Creator Account Integration (Priority: P3)

The owner converts their personal Instagram account to a Business or Creator account (free,
1-minute process in Instagram Settings). The AI Employee connects via Meta Graph API through
a custom MCP server (Instagram Platform API supports both Business and Creator accounts
since July 2024). It can
publish content (images, videos, reels with captions), read media posts, manage comments,
reply to comments, and generate engagement summaries. All posting actions require human
approval before publication.

**Why this priority**: Instagram completes the social media integration alongside Facebook.
Both use the same Meta Graph API and Developer Account, making integration efficient.

**Independent Test**: Publish a test image with caption to the Instagram Business/Creator
account via the MCP server. Retrieve recent media posts. Read comments on a post. Generate
an engagement summary.

**Acceptance Scenarios**:

1. **Given** the Instagram MCP server is configured with valid credentials, **When** the
   AI Employee invokes create_ig_post with an image URL and caption, **Then** the post
   is published to the Instagram Business/Creator account within 60 seconds after approval.

2. **Given** the Instagram MCP server is configured with valid credentials, **When** the
   AI Employee invokes get_ig_media, **Then** it returns recent posts with media type,
   caption, timestamp, and engagement metrics.

3. **Given** comments exist on an Instagram post, **When** the AI Employee invokes
   get_ig_comments, **Then** it returns comment text, author, and timestamp for each comment.

4. **Given** the AI Employee needs to reply to a comment, **When** it creates an approval
   request for the reply, **Then** the reply is sent only after human approval.

5. **Given** a post or reply action is initiated, **When** the system creates an approval
   request, **Then** the content is NOT published until the owner moves the approval file
   to Approved/.

6. **Given** the Instagram account is not converted to Business or Creator, **When** the MCP
   server attempts API calls, **Then** it provides a clear error message explaining the requirement.

---

### User Story 4 — Cross-Domain Integration (Priority: P4)

The AI Employee connects Personal domain (Gmail, WhatsApp from Silver tier) with Business
domain (Odoo, Facebook, Instagram from Gold tier). A single trigger in one domain can
cascade actions across multiple domains. For example, a client email requesting an invoice
triggers Odoo invoice creation, email delivery, and social media acknowledgment.

**Why this priority**: Cross-domain integration is the defining feature of Gold tier. It
transforms isolated tools into a cohesive autonomous employee that handles end-to-end
business workflows.

**Independent Test**: Send an email requesting an invoice. Verify the AI Employee creates
an Odoo invoice, sends it via email MCP, and logs the complete workflow across domains.

**Acceptance Scenarios**:

1. **Given** a client email arrives requesting an invoice, **When** the AI Employee
   processes it, **Then** it creates an invoice in Odoo, sends it via email (after approval),
   and logs all actions in the audit trail.

2. **Given** a WhatsApp message confirms payment received, **When** the AI Employee
   processes it, **Then** it marks the corresponding Odoo invoice as "Paid" and updates
   the Dashboard with the payment confirmation.

3. **Given** a cross-domain workflow has 5 steps, **When** step 3 fails, **Then** the
   completed steps are preserved, the failure is logged, and the owner is notified with
   the option to retry from the failed step.

4. **Given** multiple triggers arrive simultaneously from different domains, **When** the
   orchestrator processes them, **Then** each trigger is handled independently without
   blocking or corrupting other workflows.

---

### User Story 5 — Weekly CEO Briefing Generation (Priority: P5)

Every Sunday night, a scheduled task triggers the AI Employee to collect data from all
domains (Odoo financial data, social media metrics, communication summaries) and generate
a comprehensive "Monday Morning CEO Briefing" report. The report is saved to the vault
and optionally emailed to the owner.

**Why this priority**: The CEO Briefing is the showcase feature of Gold tier — it
demonstrates true autonomous business intelligence by synthesizing data across all
integrated domains into actionable insights.

**Independent Test**: Manually trigger the CEO Briefing generation. Verify it pulls data
from Odoo, Facebook, Instagram, Gmail, and WhatsApp, and produces a well-formatted
markdown report with revenue, social metrics, communication summary, and action items.

**Acceptance Scenarios**:

1. **Given** Odoo has financial data for the week, **When** the CEO Briefing is generated,
   **Then** the report includes total revenue, pending invoices, expenses, and net profit
   for the week with comparison to business goals.

2. **Given** Facebook and Instagram have posts from the week, **When** the CEO Briefing
   is generated, **Then** the report includes total posts, reach, engagement metrics,
   and top-performing content.

3. **Given** Gmail and WhatsApp had activity during the week, **When** the CEO Briefing
   is generated, **Then** the report includes new clients contacted, pending responses,
   and important conversations summary.

4. **Given** a data source is unavailable (e.g., Odoo is down), **When** the CEO Briefing
   is generated, **Then** it includes data from available sources and notes which sources
   were unavailable, rather than failing entirely.

---

### User Story 6 — Comprehensive Audit Logging (Priority: P6)

Every action the AI Employee takes is logged in structured JSON format with timestamp,
action type, actor, target, parameters, approval status, and result. Logs are stored
in the vault and retained for minimum 90 days. This provides complete traceability
and accountability for all autonomous actions.

**Why this priority**: Audit logging is essential for security, debugging, and compliance.
Without comprehensive logging, the autonomous system cannot be trusted or troubleshot.

**Independent Test**: Trigger several actions (email send, Odoo invoice, Facebook post).
Verify each action creates a structured JSON log entry with all required fields.

**Acceptance Scenarios**:

1. **Given** the AI Employee performs any action, **When** the action completes (success
   or failure), **Then** a JSON log entry is created with: timestamp, action_type, actor,
   target, parameters, approval_status, result, duration_ms, and mcp_server.

2. **Given** logs exist for the past week, **When** the owner queries logs by date or
   action type, **Then** matching entries are returned in chronological order.

3. **Given** an action fails, **When** the error is logged, **Then** the log entry includes
   error_message, stack_trace (if available), and retry_count.

4. **Given** logs are older than 90 days, **When** the retention policy runs, **Then**
   old logs are archived or deleted per the configured retention policy.

---

### User Story 7 — Error Recovery and Graceful Degradation (Priority: P7)

When any component fails (API timeout, authentication error, service unavailable), the
system recovers gracefully without crashing. Transient errors are retried with exponential
backoff. Critical failures alert the owner. The system continues operating with reduced
functionality when individual components are down.

**Why this priority**: Autonomous systems must handle failures gracefully. A system that
crashes when one API is temporarily down is not production-ready.

**Independent Test**: Disconnect Odoo Docker container while the system is running. Verify
the system continues processing emails and WhatsApp messages, logs the Odoo failure, and
resumes Odoo operations when the container is restarted.

**Acceptance Scenarios**:

1. **Given** a transient error occurs (network timeout, rate limit), **When** the system
   retries, **Then** it uses exponential backoff (1s, 2s, 4s...) up to 3 attempts before
   marking the action as failed.

2. **Given** Odoo is down, **When** the system receives an invoice request, **Then** it
   queues the request, continues processing other domain tasks, and retries the Odoo
   action when connectivity is restored.

3. **Given** Meta Graph API returns an authentication error, **When** the system detects
   it, **Then** it pauses Facebook/Instagram operations, creates a notification file
   for the owner, and continues other domain operations.

4. **Given** multiple components fail simultaneously, **When** the system assesses the
   situation, **Then** it degrades to the highest functional level possible and provides
   a clear status report in Dashboard.md.

---

### User Story 8 — Ralph Wiggum Loop (Priority: P8)

For complex multi-step tasks, the AI Employee executes autonomously without stopping
at each step for user input. The Ralph Wiggum pattern uses a Stop hook that checks
whether the task file has been moved to /Done. If not, the loop continues until the
task is complete or the maximum iteration limit is reached. Critical actions within
the loop still require human approval.

**Why this priority**: The Ralph Wiggum loop enables true autonomous multi-step task
completion — the hallmark of an "Autonomous Employee" that can handle end-to-end workflows.

**Independent Test**: Create a multi-step task (e.g., "Process invoice request: create invoice,
send email, update Odoo, post summary"). Verify the AI Employee completes all steps
autonomously, stopping only for approval-required steps.

**Acceptance Scenarios**:

1. **Given** a multi-step task is assigned, **When** the Ralph Wiggum loop starts, **Then**
   the AI Employee executes steps sequentially until the task file moves to /Done or
   max iterations (default: 10) is reached.

2. **Given** a step within the loop requires human approval (e.g., sending email), **When**
   the AI Employee reaches that step, **Then** it creates an approval file and waits
   for approval before continuing to the next step.

3. **Given** the max iteration limit is reached, **When** the loop detects this, **Then**
   it stops execution, logs the incomplete state, and notifies the owner.

4. **Given** an error occurs during a loop iteration, **When** the AI Employee detects
   the failure, **Then** it logs the error, attempts recovery, and continues the loop
   if possible or stops gracefully if not.

---

### User Story 9 — Multiple MCP Servers Architecture (Priority: P9)

The system runs multiple custom MCP servers, each handling a specific domain. All MCP
servers are registered in .mcp.json and managed by the orchestrator. Each server is
independently startable, stoppable, and monitorable.

**Why this priority**: Multiple MCP servers enable the modular, domain-specific architecture
required for cross-domain integration. Each server is a self-contained unit of functionality.

**Independent Test**: Start all MCP servers. Verify each responds to health check calls.
Send a request to each server and verify correct domain-specific responses.

**Acceptance Scenarios**:

1. **Given** all MCP servers are configured in .mcp.json, **When** Claude Code starts,
   **Then** it successfully connects to all registered MCP servers (fte-email, fte-facebook,
   fte-instagram, fte-odoo).

2. **Given** an MCP server crashes, **When** the orchestrator detects the failure, **Then**
   it logs the error, attempts restart, and other MCP servers continue operating normally.

3. **Given** a new MCP server is added to .mcp.json, **When** the system restarts, **Then**
   the new server is available to Claude Code without code changes.

4. **Given** credentials for an MCP server are stored in .env, **When** the server starts,
   **Then** it reads credentials from environment variables and never exposes them in logs.

---

### User Story 10 — Enhanced Dashboard and Agent Skills (Priority: P10)

Dashboard.md is updated to show all Gold tier metrics: financial summary from Odoo,
social media stats from Facebook/Instagram, cross-domain workflow status, and system
health. All new AI functionality is implemented as reusable Agent Skills.

**Why this priority**: The dashboard provides visibility into the expanded system, and
Agent Skills ensure all AI logic is reusable and maintainable.

**Independent Test**: Open Dashboard.md after running the system for a day. Verify it
shows Odoo financial data, social media metrics, and system health for all components.

**Acceptance Scenarios**:

1. **Given** Odoo has financial data, **When** Dashboard.md is refreshed, **Then** it
   shows current revenue, pending invoices, and recent transactions.

2. **Given** Facebook/Instagram posts were made, **When** Dashboard.md is refreshed,
   **Then** it shows post count, engagement metrics, and last post timestamp per platform.

3. **Given** new Gold tier functionality exists, **When** checking .claude/skills/,
   **Then** each domain has a corresponding skill file (odoo_accountant.md,
   facebook_poster.md, instagram_manager.md, ceo_briefing.md, audit_logger.md).

4. **Given** a skill file is updated with new instructions, **When** the AI Employee
   processes the next relevant task, **Then** it follows the updated skill instructions.

---

### User Story 11 — OPTIONAL: Twitter/X via Playwright (Priority: P11-OPTIONAL)

If time permits, the AI Employee can post to Twitter/X using Playwright browser
automation on a test account. This is NOT a core Gold tier requirement and is only
implemented after all core features are complete.

**Why this priority**: Optional — Twitter API costs $100/month. Playwright provides
a free demo-capable alternative, but carries account ban risk and is not production-ready.

**Independent Test**: Post a test tweet via Playwright on a test Twitter account. Verify
the tweet appears on the account.

**Acceptance Scenarios**:

1. **Given** a test Twitter account is logged in via Playwright, **When** the AI Employee
   invokes post_tweet, **Then** the tweet appears on the account within 60 seconds.

2. **Given** a tweet action is initiated, **When** the system creates an approval request,
   **Then** the tweet is NOT posted until the owner approves.

---

### User Story 12 — OPTIONAL: Personal Facebook Profile via Playwright (Priority: P12-OPTIONAL)

If time permits, the AI Employee can post to the owner's personal Facebook profile using
Playwright browser automation. This is NOT a core Gold tier requirement.

**Why this priority**: Optional — Meta Graph API does not support personal profiles.
Playwright provides a workaround but carries account ban risk.

**Acceptance Scenarios**:

1. **Given** the owner's Facebook is logged in via Playwright, **When** the AI Employee
   invokes post_to_profile, **Then** the post appears on the personal profile.

2. **Given** a profile post action is initiated, **When** the system creates an approval
   request, **Then** the post is NOT published until the owner approves.

---

### Edge Cases

- What happens when Odoo Docker container stops unexpectedly?
  System queues Odoo-related tasks, continues other domain operations, notifies owner,
  and retries when Odoo is back online.

- What happens when Meta Graph API rate limit is hit?
  System logs the rate limit error, pauses Facebook/Instagram operations for the
  specified cooldown period, and resumes automatically.

- What happens when the CEO Briefing has no data for a domain?
  The report is still generated with available data; missing domains are noted with
  "No data available — [reason]" rather than failing.

- What happens when the Ralph Wiggum loop encounters an unrecoverable error?
  The loop stops, logs the full state (completed steps, failed step, remaining steps),
  and creates a notification file for the owner.

- What happens when two MCP servers try to access the same resource?
  Actions are serialized through the orchestrator — no concurrent access to shared
  resources. Each action completes before the next begins.

- What happens when Odoo JSON-RPC API changes between versions?
  The Odoo MCP server uses a versioned API client; version mismatches are detected
  at startup and logged with upgrade instructions.

- What happens when audit logs consume too much disk space?
  A retention policy (configurable, default 90 days) archives or deletes old logs.
  Dashboard shows disk usage warning when logs exceed configured threshold.

- What happens when the weekly CEO Briefing scheduled task misses its window?
  Missed briefings are detected on next orchestrator cycle and generated immediately
  with a "delayed" flag in the report metadata.

---

## Requirements *(mandatory)*

### Functional Requirements

**Odoo Accounting Integration:**

- **FR-001**: System MUST deploy Odoo Community Edition via Docker (docker-compose)
  with PostgreSQL database on the owner's local machine.

- **FR-002**: System MUST provide a custom Odoo MCP server that communicates via
  Odoo's JSON-RPC API (External API, Odoo 19+).

- **FR-003**: Odoo MCP server MUST expose these tools: create_invoice, get_invoices,
  mark_payment_received, get_weekly_summary, get_expenses, create_expense.

- **FR-004**: All Odoo credentials MUST be stored in .env file, never hardcoded or
  stored in the vault.

**Facebook Business Page Integration:**

- **FR-005**: System MUST provide a custom Facebook MCP server that communicates via
  Meta Graph API (v18.0+).

- **FR-006**: Facebook MCP server MUST expose: create_page_post, get_page_posts,
  get_post_comments, reply_to_comment, get_page_insights.

- **FR-007**: Facebook MCP server MUST use owner-managed access tokens stored in .env.

- **FR-008**: All Facebook post actions MUST require human approval before execution.

**Instagram Business/Creator Account Integration:**

- **FR-009**: System MUST provide a custom Instagram MCP server that communicates via
  Meta Graph API.

- **FR-010**: Instagram MCP server MUST expose: create_ig_post, create_ig_reel,
  get_ig_media, get_ig_comments, reply_ig_comment, get_ig_insights.

- **FR-011**: Instagram MCP server MUST require the account to be converted to
  Business or Creator type.

- **FR-011a**: All Instagram post/reel actions MUST require human approval before
  publication.

**Cross-Domain Integration:**

- **FR-012**: System MUST support cross-domain workflows where a trigger in one domain
  (Personal: Gmail, WhatsApp) cascades actions to another domain (Business: Odoo,
  Facebook, Instagram).

- **FR-013**: Each cross-domain workflow MUST be traceable through audit logs with
  a shared workflow_id linking all related actions.

- **FR-014**: Cross-domain workflows MUST handle partial failures — completed steps
  are preserved when a later step fails.

**Weekly CEO Briefing:**

- **FR-015**: System MUST generate a weekly CEO Briefing every Sunday night via
  scheduled task (APScheduler).

- **FR-016**: CEO Briefing MUST include: financial summary (from Odoo), social media
  metrics (from Facebook/Instagram), communication summary (from Gmail/WhatsApp),
  action items, and proactive suggestions.

- **FR-017**: CEO Briefing MUST be saved as markdown in vault/Briefings/ and
  optionally emailed to the owner.

- **FR-018**: CEO Briefing MUST handle missing data sources gracefully — include
  available data and note unavailable sources.

**Comprehensive Audit Logging:**

- **FR-019**: Every AI action MUST create a structured JSON log entry with: timestamp,
  action_type, actor, target, parameters, approval_status, result, duration_ms,
  mcp_server, and workflow_id (if applicable).

- **FR-020**: Logs MUST be stored in vault/Logs/YYYY-MM-DD.json files.

- **FR-021**: Logs MUST be retained for minimum 90 days with configurable retention policy.

- **FR-022**: Log entries MUST never contain sensitive data (passwords, tokens, full
  credit card numbers).

**Error Recovery and Graceful Degradation:**

- **FR-023**: System MUST implement exponential backoff retry for transient errors
  (network timeout, rate limit) — 3 attempts with delays of 1s, 2s, 4s.

- **FR-024**: System MUST continue operating when individual components fail — other
  domain operations proceed normally.

- **FR-025**: System MUST create notification files for critical failures requiring
  human attention.

- **FR-026**: System MUST never auto-retry payment or financial actions — always
  require fresh human approval.

**Ralph Wiggum Loop:**

- **FR-027**: System MUST implement the Ralph Wiggum Stop hook pattern for autonomous
  multi-step task completion.

- **FR-028**: Loop completion MUST use file-movement strategy — task is complete when
  the task file moves to /Done.

- **FR-029**: Loop MUST have a configurable maximum iteration limit (default: 10) to
  prevent infinite loops.

- **FR-030**: Critical actions within the loop (payments, external sends) MUST still
  require human approval via the existing approval workflow.

**Multiple MCP Servers:**

- **FR-031**: System MUST register all MCP servers in .mcp.json: fte-email (existing),
  fte-facebook (new), fte-instagram (new), fte-odoo (new).

- **FR-032**: Each MCP server MUST be independently startable and stoppable.

- **FR-033**: MCP server credentials MUST be loaded from environment variables (.env).

**Dashboard and Agent Skills:**

- **FR-034**: Dashboard.md MUST show Odoo financial summary, social media metrics per
  platform, cross-domain workflow status, and system health for all MCP servers.

- **FR-035**: All Gold tier AI functionality MUST be implemented as Agent Skills in
  .claude/skills/: odoo_accountant.md, facebook_poster.md, instagram_manager.md,
  ceo_briefing.md, audit_logger.md, error_handler.md.

**Documentation:**

- **FR-036**: System MUST include architecture documentation covering system design,
  MCP server structure, data flows, and integration points.

- **FR-037**: System MUST include lessons learned documentation covering challenges,
  solutions, and recommendations for future development.

**OPTIONAL Features:**

- **FR-038**: (OPTIONAL) System MAY support Twitter/X posting via Playwright browser
  automation on a test account.

- **FR-039**: (OPTIONAL) System MAY support personal Facebook profile posting via
  Playwright browser automation.

---

### Key Entities

- **Odoo Invoice**: Financial record in Odoo containing client name, amount, due date,
  status (Draft/Sent/Paid), and payment history. Created and managed via JSON-RPC API.

- **Facebook Page Post**: Social media content published on the owner's Facebook Business
  Page via Meta Graph API. Contains message text, timestamp, and engagement metrics.

- **Instagram Media**: Content on the owner's Instagram Business/Creator Account. Contains media
  type, caption, timestamp, likes, and comments.

- **CEO Briefing**: Weekly markdown report synthesizing data from all integrated domains
  (Odoo, Facebook, Instagram, Gmail, WhatsApp) into business insights and action items.

- **Audit Log Entry**: Structured JSON record of every AI action with timestamp, type,
  actor, target, parameters, approval status, result, and workflow linkage.

- **Cross-Domain Workflow**: A sequence of actions spanning multiple domains (Personal +
  Business) linked by a shared workflow_id for traceability.

- **MCP Server**: Custom Python process exposing domain-specific tools via Model Context
  Protocol. Each server handles one domain (email, Facebook, Instagram, Odoo).

- **Agent Skill (Gold)**: Markdown file in .claude/skills/ defining reusable AI procedure.
  Gold tier adds: odoo_accountant, facebook_poster, instagram_manager, ceo_briefing,
  audit_logger, error_handler.

- **Ralph Wiggum State File**: Task file that the Stop hook monitors. When the file moves
  to /Done, the autonomous loop completes. Contains task description, steps, and status.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Odoo invoices are created within 30 seconds of request via MCP server —
  verified by creating 5 test invoices and checking Odoo web interface.

- **SC-002**: Facebook Business Page posts appear within 60 seconds of approval —
  verified with 3 test posts.

- **SC-003**: Instagram engagement data (media, comments) is retrievable via MCP server —
  verified by fetching data from an account with existing posts.

- **SC-004**: A single email trigger (invoice request) cascades correctly across Odoo
  (invoice created) + Email (invoice sent) + Audit log (all steps recorded) — verified
  with 3 end-to-end cross-domain workflows.

- **SC-005**: CEO Briefing generates a complete report with data from all available
  domains within 5 minutes — verified by manual trigger and content review.

- **SC-006**: Every AI action produces a structured JSON audit log entry with all
  required fields — verified by reviewing logs after 20+ diverse actions.

- **SC-007**: System continues operating when one component is down (e.g., Odoo stopped)
  — verified by stopping Odoo Docker and confirming email/WhatsApp processing continues.

- **SC-008**: Ralph Wiggum loop completes a 5-step cross-domain task autonomously
  (pausing only for approval steps) — verified with 3 multi-step task executions.

- **SC-009**: All 4 MCP servers (email, facebook, instagram, odoo) start successfully
  and respond to tool calls — verified by invoking each server's primary tool.

- **SC-010**: Dashboard.md accurately shows Odoo financial data, social media metrics,
  and system health within 2 minutes of data changes — verified by comparing dashboard
  content with source system data.

- **SC-011**: All Gold tier Agent Skills exist in .claude/skills/ and are correctly
  invoked during appropriate workflows — verified by skill invocation audit logs.

- **SC-012**: Architecture documentation clearly describes system design, MCP server
  structure, and data flows — verified by an independent reader understanding the
  system from documentation alone.

---

## Assumptions

- Silver tier is fully implemented and functional before Gold tier begins.
- The owner has Docker and docker-compose installed on their local machine (WSL).
- The owner can create a Facebook Business Page (free) and convert their Instagram
  account to Business or Creator (free).
- The owner can create a Meta Developer Account (free) and generate access tokens.
- Odoo Community Edition 19+ is available as a Docker image.
- The owner's machine has sufficient resources to run Odoo Docker alongside existing services.
- Meta Graph API v18.0+ is stable and available for Page management and Instagram.
- JSON-RPC API for Odoo 19+ is documented and accessible.
- The owner will manually set up initial Odoo configuration (company, chart of accounts)
  via Odoo's web interface before API integration.
- Weekly CEO Briefing runs on Sunday night; the owner reviews it Monday morning.
- Audit log retention of 90 days is sufficient for compliance and debugging needs.
- Ralph Wiggum loop maximum of 10 iterations is sufficient for most multi-step tasks.

---

## Out of Scope (Gold Tier)

- Cloud deployment or always-on hosting (Platinum tier)
- Work-Zone Specialization / Cloud-Local split (Platinum tier)
- Agent-to-Agent (A2A) communication protocol (Platinum tier)
- Vault syncing between Cloud and Local (Platinum tier)
- Deploying Odoo on Cloud VM with HTTPS (Platinum tier)
- Payment processing via banking APIs (requires separate banking integration)
- Voice message transcription
- Calendar integration and meeting scheduling
- Advanced AI model fine-tuning or custom training
- Mobile app or web UI beyond Obsidian dashboard

---

## Pre-Implementation Setup Required

Before implementation begins, the owner must complete these setup steps:

1. **Docker Setup**: Verify Docker and docker-compose are installed in WSL
2. **Facebook Business Page**: Create a Business Page on Facebook (free, 2 minutes)
3. **Instagram Account**: Convert personal Instagram to Business or Creator account (free, 1 minute)
4. **Meta Developer Account**: Create account at developers.facebook.com (free)
5. **Meta App**: Create an app in Meta Developer Portal and obtain access tokens
6. **Odoo Initial Config**: After Docker setup, configure Odoo company basics via web UI

---

## Dependency Chain

```
Silver Tier (complete)
    └── Gold Tier
        ├── Odoo Docker + MCP (P1) ───────────────┐
        ├── Facebook MCP (P2) ────────────────────┤
        ├── Instagram MCP (P3) ───────────────────┤
        ├── Cross-Domain Integration (P4) ────────┼── Requires P1+P2+P3
        ├── CEO Briefing (P5) ────────────────────┼── Requires P4 (all domains)
        ├── Audit Logging (P6) ───────────────────┤── Can start early, enhances all
        ├── Error Recovery (P7) ──────────────────┤── Can start early, enhances all
        ├── Ralph Wiggum Loop (P8) ───────────────┼── Requires P4+P6+P7
        ├── Multiple MCP Servers (P9) ────────────┼── Architecture for P1+P2+P3
        ├── Dashboard + Skills (P10) ─────────────┼── Requires all above
        ├── [OPTIONAL] Twitter Playwright (P11) ──┤── Only if time permits
        └── [OPTIONAL] Personal FB Playwright (P12)┘── Only if time permits
```

---

## New Agent Skills (Gold Tier)

| Skill | Purpose |
|-------|---------|
| odoo_accountant.md | Create invoices, track payments, generate financial summaries |
| facebook_poster.md | Create Facebook Page posts, read comments, generate engagement summaries |
| instagram_manager.md | Read Instagram media, manage comments, generate engagement summaries |
| ceo_briefing.md | Generate weekly CEO Briefing from all domain data |
| audit_logger.md | Log every AI action in structured JSON format |
| error_handler.md | Handle errors with retry logic, graceful degradation, and notifications |
