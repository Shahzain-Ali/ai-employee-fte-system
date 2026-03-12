# Feature Specification: Hackathon-0 Platinum Tier — Always-On Cloud + Local Executive

**Feature Branch**: `004-platinum-cloud-local`
**Created**: 2026-03-09
**Status**: Draft
**Input**: Platinum Tier: Always-On Cloud + Local Executive — Extends Gold tier with 24/7 cloud
deployment (Oracle Cloud Free Tier), Work-Zone Specialization (Cloud drafts / Local approves),
Git-synced Vault for agent delegation, security-first vault sync (.gitignore sensitive data),
Odoo on Cloud VM with HTTPS, optional A2A upgrade (skipped — file-based sufficient),
and Platinum Demo (email → cloud draft → sync → local approve → send).

---

## Official Requirements (Hackathon Documentation Page 5)

**Platinum Tier: Always-On Cloud + Local Executive** — Estimated time: 60+ hours

1. All Gold requirements plus:
2. Deploy your AI employee on a cloud VM (Oracle Free Tier or AWS) so it runs 24/7
   (watchers + orchestrator + health monitoring)
3. Work-Zone Specialization: Cloud Agent owns drafts; Local Agent owns approvals and
   sensitive actions (WhatsApp, banking, final send/post)
4. Delegation via Synced Vault (Phase 1): Agents communicate through files in a
   Git-synced shared folder with claim-by-move and single-writer rules
5. Security Rule: Vault sync includes only markdown/state files; secrets (.env, tokens,
   WhatsApp sessions, banking credentials) NEVER leave the local machine
6. Deploy Odoo Community on a Cloud VM with HTTPS (Let's Encrypt), automatic backups,
   and health monitoring
7. Optional: A2A Upgrade (Phase 2) — Direct agent-to-agent messaging instead of
   file-based (SKIPPED — file-based is sufficient for this use case)
8. Platinum Demo (minimum passing gate): Email arrives while laptop is off → Cloud
   drafts reply → Git sync → Local approves when laptop returns → Email sent via MCP →
   Logged → Done

---

## Decisions & Context

### Decisions Made During Discussion (2026-03-09)

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Cloud Provider | Oracle Cloud Free Tier (ARM A1: 4 OCPUs, 24GB RAM) | Forever-free, sufficient for Odoo + watchers + Claude Code |
| Cloud OS | Ubuntu 22.04+ on ARM A1 | Stable LTS, well-supported, Oracle default |
| AI Agent Engine | Claude Code (`claude -p "prompt"` headless mode) | Official doc: "Must use Claude Code as the primary reasoning engine" |
| Programmatic Triggering | `claude-agent-sdk` (Python) | Orchestrator triggers Claude Code via Python SDK |
| Vault Sync Method | Hybrid: event-based push (gitwatch/inotifywait) + timer-based pull (every 2-3 min) | Avoids wasteful constant push when no changes; pulls on schedule to catch remote updates |
| Sync Intermediary | GitHub private repository | Cloud pushes → GitHub ← Local pulls (and vice versa) |
| A2A Upgrade | SKIPPED | Cloud deployed because laptop is offline; A2A needs both online = rare scenario, no real benefit |
| HTTPS for Odoo | Let's Encrypt (certbot) + Nginx reverse proxy | Free SSL, auto-renewal, industry standard |
| Health Monitoring | Simple Python/bash script with cron | Checks Odoo, watchers, disk, RAM; auto-restart on failure |
| Local Auto-Start | Windows Task Scheduler → WSL → Orchestrator | Laptop ON = orchestrator auto-starts in background |
| Process Management (Cloud) | PM2 or systemd | Auto-restart on crash, startup persistence, log management |
| Dashboard Write Rule | Single-writer: Local Agent only | Prevents file corruption from concurrent writes |
| Conflict Resolution | Claim-by-move rule (first to move file owns task) | Prevents duplicate work between Cloud and Local agents |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Platinum Demo: End-to-End Email Flow (Priority: P1)

The owner's laptop is OFF (sleeping/shutdown). A client sends an email. The Cloud Agent
(running 24/7 on Oracle Cloud) detects the email via the Email Watcher, processes it with
Claude Code (headless), drafts a professional reply, and saves the draft to
`/Pending_Approval/email/` in the synced vault. Cloud Agent pushes to GitHub. When the
owner turns on their laptop next morning, the Local Orchestrator auto-starts, pulls from
GitHub, detects the pending approval, and notifies the owner. The owner reviews the draft,
approves it, and the Local Agent sends the email via the Email MCP server. The action is
logged and the task file moves to `/Done/`.

**Why this priority**: This IS the Platinum Demo — the minimum passing gate for the tier.
If this works end-to-end, Platinum is achieved. Every other user story supports this flow.

**Independent Test**: Turn off laptop. Send a test email. Verify Cloud creates draft in
vault and pushes to GitHub. Turn on laptop. Verify Local pulls, shows notification,
sends email after approval, and logs the complete flow.

**Acceptance Scenarios**:

1. **Given** the laptop is OFF and Cloud Agent is running on Oracle Cloud, **When** a
   client email arrives, **Then** the Email Watcher detects it within 2 minutes and
   triggers the Orchestrator.

2. **Given** the Cloud Orchestrator receives an email trigger, **When** it invokes
   Claude Code via `claude -p` or `claude-agent-sdk`, **Then** Claude Code reads the
   email content, checks Company_Handbook.md for context, and generates a professional
   draft reply saved to `/Pending_Approval/email/draft_<id>.md`.

3. **Given** a draft file is created in the vault, **When** the Git sync event fires,
   **Then** the file is pushed to GitHub within 60 seconds.

4. **Given** the owner turns on their laptop, **When** the Local Orchestrator auto-starts
   (via Windows Task Scheduler → WSL), **Then** it performs a git pull within 2-3 minutes
   and detects the pending approval file.

5. **Given** the Local Agent detects a pending approval, **When** the owner reviews and
   approves the draft, **Then** the Local Agent sends the email via the Email MCP server
   (`fte-email`) and the email is delivered to the client.

6. **Given** the email is sent successfully, **When** the Local Agent completes the action,
   **Then** it creates a structured JSON audit log entry and moves the task file from
   `/Pending_Approval/email/` to `/Done/email/`.

---

### User Story 2 — Cloud 24/7 Deployment on Oracle Cloud (Priority: P2)

The AI Employee system (watchers, orchestrator, Claude Code access, health monitoring)
is deployed on an Oracle Cloud Free Tier ARM A1 VM and runs continuously 24/7. The
system auto-restarts on crash via PM2 or systemd. SSH access is secured. The VM runs
Ubuntu 22.04+ with Python 3.12+, uv, and all required dependencies.

**Why this priority**: Without the cloud VM running 24/7, the Platinum Demo cannot work.
This is the infrastructure foundation for everything else.

**Independent Test**: SSH into the Oracle Cloud VM. Verify watchers are running, orchestrator
is active, Claude Code responds to `claude -p "hello"`, and health monitor is checking
all components. Reboot the VM and verify all services auto-restart.

**Acceptance Scenarios**:

1. **Given** an Oracle Cloud Free Tier ARM A1 VM is provisioned, **When** the deployment
   script completes, **Then** Python 3.12+, uv, Claude Code CLI, and all project
   dependencies are installed and functional.

2. **Given** the VM is running, **When** all services are started via PM2/systemd, **Then**
   the Email Watcher, Social Media Watchers, Orchestrator, and Health Monitor are all
   active and logging their status.

3. **Given** a service crashes unexpectedly, **When** PM2/systemd detects the failure,
   **Then** the service is automatically restarted within 30 seconds.

4. **Given** the VM is rebooted, **When** it comes back online, **Then** all services
   auto-start without manual intervention.

5. **Given** Claude Code is installed on the VM, **When** the Orchestrator invokes
   `claude -p "process this email: ..."`, **Then** Claude Code returns a structured
   response within the API timeout period.

---

### User Story 3 — Work-Zone Specialization (Priority: P3)

The system enforces strict domain ownership: Cloud Agent handles ONLY drafts and
read-only operations (email triage, social media draft posts, invoice draft creation,
scheduling suggestions). Local Agent handles ALL final actions (email send, social media
publish, WhatsApp messages, banking/payments, dashboard updates) and all sensitive
operations requiring credentials that never leave the local machine.

**Why this priority**: Work-Zone Specialization is the security architecture of Platinum.
Without it, sensitive credentials would be on the cloud (security risk) or the cloud
agent would send unauthorized messages (business risk).

**Independent Test**: Verify Cloud Agent can create draft files but CANNOT invoke send/publish
MCP tools. Verify Local Agent can approve and execute final actions. Attempt to make Cloud
Agent send an email directly — it must fail.

**Acceptance Scenarios**:

1. **Given** the Cloud Agent receives an email that needs a reply, **When** it processes
   the email, **Then** it creates a draft file in `/Pending_Approval/email/` but does
   NOT invoke the Email MCP `send_email_tool` directly.

2. **Given** the Cloud Agent detects a social media engagement opportunity, **When** it
   drafts a post, **Then** it saves the draft to `/Pending_Approval/social/` but does
   NOT invoke `create_page_post` or `create_ig_post` directly.

3. **Given** a draft exists in `/Pending_Approval/`, **When** the Local Agent detects it
   after git pull, **Then** it presents the draft for owner review and only executes
   the final action (send/publish) after explicit approval.

4. **Given** the Cloud Agent's configuration, **When** examining its available tools and
   permissions, **Then** it has NO access to WhatsApp sessions, banking credentials,
   or direct send/publish MCP tools.

5. **Given** the Local Agent is processing approvals, **When** it updates the dashboard,
   **Then** ONLY the Local Agent writes to Dashboard.md (single-writer rule). Cloud
   Agent writes status updates to `/Updates/` folder instead.

---

### User Story 4 — Git-Synced Vault with Claim-by-Move (Priority: P4)

A shared vault directory is synchronized between Cloud and Local via Git (GitHub as
intermediary). The vault has a structured folder hierarchy: `/Needs_Action/<domain>/`,
`/In_Progress/<agent>/`, `/Plans/<domain>/`, `/Pending_Approval/<domain>/`,
`/Updates/`, `/Done/`. The claim-by-move rule prevents duplicate work: the first agent
to move a file from `/Needs_Action/` to `/In_Progress/<agent>/` owns that task. Git
sync uses a hybrid approach: event-based push (on file change) + timer-based pull
(every 2-3 minutes).

**Why this priority**: The vault is the communication channel between Cloud and Local
agents. Without it, neither agent knows what the other is doing.

**Independent Test**: Create a file in `/Needs_Action/email/` on Cloud. Verify it syncs
to Local within 3 minutes. Move it to `/In_Progress/cloud/` on Cloud. Verify Local
sees the move and does NOT attempt to process the same task.

**Acceptance Scenarios**:

1. **Given** Cloud Agent creates a file in the vault, **When** the Git sync event fires
   (push on change), **Then** the file is committed and pushed to GitHub within 60 seconds.

2. **Given** a file was pushed to GitHub by Cloud, **When** Local's timer-based pull runs
   (every 2-3 minutes), **Then** the file appears in the Local vault directory.

3. **Given** a task file exists in `/Needs_Action/email/`, **When** Cloud Agent picks it
   up first, **Then** it moves the file to `/In_Progress/cloud/` and pushes. Local Agent
   sees the file is no longer in `/Needs_Action/` and skips it.

4. **Given** both agents check `/Needs_Action/` at roughly the same time, **When** Cloud
   moves the file first and pushes, **Then** Local's next pull shows the file in
   `/In_Progress/cloud/` and Local does NOT create a duplicate task.

5. **Given** Cloud Agent completes a draft, **When** it moves the file to
   `/Pending_Approval/<domain>/`, **Then** the move is synced and Local Agent detects
   the new approval-pending item on its next pull.

6. **Given** Local Agent writes to `/Updates/` instead of Dashboard.md, **When** the
   Cloud Agent needs status information, **Then** it reads from `/Updates/` (not
   Dashboard.md) respecting the single-writer rule.

---

### User Story 5 — Security: Vault Sync Excludes Sensitive Data (Priority: P5)

The `.gitignore` file is configured BEFORE the first sync to exclude all sensitive files:
`.env`, OAuth tokens, WhatsApp session data, banking credentials, API keys, Odoo database
credentials. Only markdown files, state files, and log files are synced. This ensures
that even if the cloud VM is compromised, no sensitive credentials are exposed.

**Why this priority**: Security is non-negotiable. A single leaked credential could
compromise the owner's email, social media, bank account, or WhatsApp. This MUST be
configured before any sync happens.

**Independent Test**: Run `git status` in the vault. Verify `.env`, token files, and
session files are NOT tracked. Attempt to `git add .env` — it must be rejected by
`.gitignore`. Push the vault to GitHub and verify no sensitive files appear in the
remote repository.

**Acceptance Scenarios**:

1. **Given** the vault `.gitignore` is configured, **When** listing ignored patterns,
   **Then** it includes at minimum: `.env`, `*.token`, `*.session`, `*credentials*`,
   `*.key`, `*.pem`, `whatsapp-session/`, `banking/`, and any path containing `secret`.

2. **Given** the vault is synced to GitHub, **When** examining the remote repository
   contents, **Then** NO files containing passwords, API keys, OAuth tokens, or
   session data are present.

3. **Given** a developer accidentally places a `.env` file in the vault, **When** they
   run `git add .`, **Then** the `.env` file is NOT staged for commit due to `.gitignore`.

4. **Given** the Cloud Agent needs to access an API (e.g., Gmail), **When** it reads
   credentials, **Then** it reads from its OWN local `.env` file on the Cloud VM (not
   synced from the vault). Cloud and Local each maintain their OWN `.env` files independently.

5. **Given** vault sync is operational, **When** auditing synced file types, **Then**
   ONLY `.md`, `.json` (logs), and `.txt` state files are present in Git history.

---

### User Story 6 — Odoo on Cloud VM with HTTPS (Priority: P6)

Odoo Community Edition (currently running locally via Docker in Gold Tier) is migrated
to the Oracle Cloud VM. It runs 24/7 with HTTPS enabled via Let's Encrypt (certbot) and
Nginx reverse proxy. Automatic database backups are configured. Health monitoring checks
Odoo availability and auto-restarts on failure. The existing Odoo MCP server connection
URL changes from `http://localhost:8069` to `https://odoo.<domain>` (or Cloud VM IP with
HTTPS).

**Why this priority**: Odoo on cloud ensures 24/7 availability for invoice processing,
financial reporting, and CEO Briefing generation — even when the laptop is off.

**Independent Test**: Access Odoo via `https://odoo.<domain>` from a browser. Create an
invoice via the Odoo MCP server pointing to the cloud URL. Verify HTTPS certificate is
valid. Stop Odoo process — verify health monitor restarts it within 60 seconds.

**Acceptance Scenarios**:

1. **Given** Odoo is deployed on the Oracle Cloud VM via Docker, **When** accessing the
   Odoo web interface, **Then** it is available at an HTTPS URL with a valid Let's Encrypt
   SSL certificate.

2. **Given** the Odoo MCP server (`fte-odoo`) is updated with the cloud URL, **When** the
   AI Employee invokes `create_invoice` via MCP, **Then** the invoice is created in the
   cloud Odoo instance successfully.

3. **Given** Odoo is running on the cloud, **When** the Odoo process crashes, **Then** the
   health monitor detects the failure and restarts Odoo within 60 seconds.

4. **Given** automatic backups are configured, **When** the backup schedule triggers
   (daily), **Then** a database backup is created and stored on the VM (or external
   storage) with date-stamped filename.

5. **Given** the Cloud Agent needs financial data, **When** it queries Odoo via MCP,
   **Then** it receives the same data quality as the previous local Odoo setup (Gold tier
   compatibility preserved).

6. **Given** the Local Agent needs to approve a financial action, **When** it connects
   to the cloud Odoo via MCP, **Then** it can perform approval-level actions (post invoice,
   confirm payment) via HTTPS.

---

### User Story 7 — Health Monitoring and Auto-Recovery (Priority: P7)

A health monitoring script runs on the Cloud VM (via cron or PM2) checking all critical
components at regular intervals (every 3-5 minutes): Odoo availability, Email Watcher
status, Social Media Watcher status, Orchestrator status, disk space, RAM usage, and
last activity timestamp. On failure, it attempts auto-restart. On repeated failure or
resource exhaustion, it sends an alert (email notification or vault file).

**Why this priority**: A 24/7 cloud system must be self-healing. Without health monitoring,
a crashed watcher could go unnoticed for hours, missing critical emails or invoices.

**Independent Test**: Stop the Email Watcher manually. Verify the health monitor detects
the failure within 5 minutes and auto-restarts it. Fill disk to 90% threshold — verify
an alert is generated.

**Acceptance Scenarios**:

1. **Given** the health monitor is running, **When** it checks all components, **Then** it
   verifies: Odoo responds to HTTP, Email Watcher process is alive, Orchestrator process
   is alive, disk usage < 85%, RAM usage < 90%, and last activity was within 30 minutes.

2. **Given** a component is detected as down, **When** the health monitor attempts restart,
   **Then** it logs the restart attempt and result. If restart succeeds, normal operation
   resumes. If restart fails 3 times, an alert is created.

3. **Given** disk space exceeds 85%, **When** the health monitor detects this, **Then** it
   creates an alert file in the vault and optionally sends an email notification to the
   owner.

4. **Given** all components are healthy, **When** the health check completes, **Then** it
   logs a "healthy" status entry with timestamp (no alert generated).

---

### User Story 8 — Local Agent Auto-Start on Laptop Boot (Priority: P8)

When the owner turns on their laptop (Windows + WSL), the Local Orchestrator automatically
starts in the background without any manual intervention. It performs an immediate git pull,
checks for pending approvals, and begins processing. The process runs invisibly in the
background (no terminal window). Windows Task Scheduler triggers WSL startup, which
launches the Local Orchestrator.

**Why this priority**: The owner should not need to manually start anything. "Turn on
laptop" = "Local Agent is ready" — seamless experience.

**Independent Test**: Restart the laptop. Without opening any terminal or running any
command, verify the Local Orchestrator is running (check WSL processes). Verify it has
already pulled latest vault changes from GitHub.

**Acceptance Scenarios**:

1. **Given** Windows Task Scheduler has the startup task configured, **When** the laptop
   boots and the user logs in, **Then** WSL starts and the Local Orchestrator begins
   running within 60 seconds of login.

2. **Given** the Local Orchestrator starts, **When** it initializes, **Then** it immediately
   performs a `git pull` to sync the vault and checks `/Pending_Approval/` for any items
   that arrived while the laptop was off.

3. **Given** there are pending approvals from the Cloud Agent, **When** the Local Orchestrator
   detects them, **Then** it creates a notification for the owner (system notification,
   dashboard update, or notification file).

4. **Given** the orchestrator is running, **When** checking system resources, **Then** it
   runs in the background consuming minimal CPU/RAM and does not interfere with normal
   laptop usage.

---

### Edge Cases

- **What happens when Cloud and Local both try to move the same file simultaneously?**
  Git merge conflict occurs. The resolution strategy: Cloud's move takes priority (it runs
  24/7 and likely moved first). Local detects the conflict on next pull, accepts Cloud's
  version, and skips the task. Conflict is logged.

- **What happens when GitHub is unreachable (network outage)?**
  Both agents continue operating locally. Pushes are queued. On reconnection, accumulated
  changes are pushed. A brief sync delay occurs but no data is lost.

- **What happens when the Oracle Cloud VM runs out of free tier resources?**
  Health monitor detects high resource usage and alerts the owner. Non-critical watchers
  can be temporarily paused. Odoo and Email Watcher are prioritized.

- **What happens when the owner's laptop is off for multiple days?**
  Cloud Agent continues processing, accumulating drafts in `/Pending_Approval/`. When
  laptop returns, Local Agent pulls ALL pending items and presents them in chronological
  order for batch review.

- **What happens when Let's Encrypt certificate expires?**
  Certbot auto-renewal is configured (cron job). If renewal fails, health monitor detects
  HTTPS errors and alerts the owner. Odoo MCP falls back to HTTP temporarily with a
  warning log.

- **What happens when Cloud Agent creates too many draft files (spam/flood)?**
  A rate limiter in the Cloud Orchestrator limits draft creation (e.g., max 20 drafts/hour).
  Excess triggers are queued or dropped with logging.

- **What happens when git sync has merge conflicts on non-task files (e.g., logs)?**
  Auto-resolve strategy: for log files, accept both changes (append). For state files,
  accept the most recent timestamp. For task files, the claim-by-move rule applies.

- **What happens when Cloud VM SSH access is compromised?**
  SSH key-only authentication (no password). Fail2ban blocks repeated attempts. No
  sensitive credentials on cloud (only `.env` with API tokens that can be rotated).
  Owner is alerted via health monitor if suspicious activity detected.

---

## Requirements *(mandatory)*

### Functional Requirements

**Cloud 24/7 Deployment:**

- **FR-001**: System MUST deploy on an Oracle Cloud Free Tier ARM A1 VM (or equivalent
  cloud VM) running Ubuntu 22.04+ with Python 3.12+, uv, and Claude Code CLI installed.

- **FR-002**: System MUST run Email Watcher, Social Media Watchers, Orchestrator, and
  Health Monitor as managed services via PM2 or systemd with auto-restart on failure.

- **FR-003**: System MUST auto-start all services on VM reboot without manual intervention.

- **FR-004**: System MUST use Claude Code in headless mode (`claude -p "prompt"` or
  `claude-agent-sdk`) as the primary reasoning engine on the cloud VM.

**Work-Zone Specialization:**

- **FR-005**: Cloud Agent MUST be restricted to draft-only operations: read emails,
  triage, create draft replies, create draft social posts, create draft invoices,
  and suggest schedules. Cloud Agent MUST NOT invoke send/publish/confirm MCP tools.

- **FR-006**: Local Agent MUST handle all final actions: email send (via `fte-email` MCP),
  social media publish (via `fte-facebook`, `fte-instagram` MCP), WhatsApp messages,
  banking/payments, and dashboard updates.

- **FR-007**: Local Agent MUST be the single writer of Dashboard.md. Cloud Agent MUST
  write status updates to `/Updates/` folder only.

- **FR-008**: Sensitive credentials (WhatsApp sessions, banking creds, personal API tokens)
  MUST exist ONLY on the Local machine, never on the Cloud VM.

**Git-Synced Vault:**

- **FR-009**: System MUST use a Git repository (GitHub private repo as intermediary) to
  sync a shared vault directory between Cloud and Local agents.

- **FR-010**: Vault MUST have this folder structure: `/Needs_Action/<domain>/`,
  `/In_Progress/<agent>/` (where agent is `cloud` or `local`),
  `/Plans/<domain>/`, `/Pending_Approval/<domain>/`, `/Updates/`, `/Done/`, `/Logs/`.

- **FR-011**: System MUST implement claim-by-move rule: the first agent to move a file
  from `/Needs_Action/` to `/In_Progress/<agent>/` owns that task. The other agent
  MUST skip files that are no longer in `/Needs_Action/`.

- **FR-012**: Git sync MUST use a hybrid approach: event-based push (triggered by file
  changes via inotifywait/gitwatch) and timer-based pull (every 2-3 minutes via cron).

- **FR-013**: Git sync MUST handle merge conflicts gracefully: auto-resolve for logs
  (append both), use claim-by-move for task files, and alert owner for unresolvable
  conflicts.

**Security (Vault Sync):**

- **FR-014**: The vault `.gitignore` MUST be configured BEFORE the first sync to exclude:
  `.env`, `*.token`, `*.session`, `*credentials*`, `*.key`, `*.pem`, `whatsapp-session/`,
  `banking/`, and any file containing secrets.

- **FR-015**: ONLY markdown (`.md`), JSON logs (`.json`), and text state files (`.txt`)
  MUST be present in Git history. Binary files, credentials, and session data MUST NOT
  be synced.

- **FR-016**: Cloud and Local MUST each maintain independent `.env` files with their own
  credentials. Cloud `.env` contains API keys for services it needs (Gmail read, social
  media read). Local `.env` contains ALL credentials including sensitive ones.

- **FR-017**: Cloud VM SSH access MUST use key-only authentication (no password login).

**Odoo on Cloud:**

- **FR-018**: Odoo Community Edition MUST be deployed on the Cloud VM via Docker
  (docker-compose) with PostgreSQL, running 24/7.

- **FR-019**: Odoo MUST be accessible via HTTPS using Let's Encrypt SSL certificate
  (certbot) with Nginx reverse proxy.

- **FR-020**: Odoo MCP server (`fte-odoo`) connection URL MUST be updated from
  `http://localhost:8069` to the cloud HTTPS URL.

- **FR-021**: Automatic daily Odoo database backups MUST be configured with date-stamped
  filenames stored on the VM.

- **FR-022**: Certbot auto-renewal MUST be configured via cron to prevent certificate
  expiration.

**Health Monitoring:**

- **FR-023**: A health monitoring script MUST run every 3-5 minutes (via cron or PM2)
  checking: Odoo HTTP response, Email Watcher process status, Orchestrator process status,
  disk usage, RAM usage, and last activity timestamp.

- **FR-024**: On component failure, health monitor MUST attempt auto-restart (up to 3
  retries). On repeated failure, it MUST create an alert notification (email and/or
  vault file).

- **FR-025**: Health monitor MUST log every check result (healthy or unhealthy) with
  timestamp for audit trail.

**Local Agent Auto-Start:**

- **FR-026**: Windows Task Scheduler MUST be configured to start WSL and the Local
  Orchestrator automatically on user login.

- **FR-027**: Local Orchestrator MUST run in the background (no visible terminal window)
  consuming minimal system resources.

- **FR-028**: On startup, Local Orchestrator MUST immediately perform `git pull` and
  check for pending approvals accumulated while the laptop was off.

**Platinum Demo Flow:**

- **FR-029**: The complete Platinum Demo flow MUST work end-to-end: email arrives →
  Cloud Watcher detects → Cloud Claude Code drafts reply → draft saved to
  `/Pending_Approval/email/` → Git push to GitHub → Local pulls on startup →
  owner reviews and approves → Local sends via Email MCP → action logged →
  task file moves to `/Done/`.

- **FR-030**: Each step of the Platinum Demo MUST be independently verifiable through
  audit logs with timestamps showing the complete timeline.

---

### Key Entities

- **Cloud Agent**: The AI Employee instance running 24/7 on Oracle Cloud VM. Consists of
  watchers (Python scripts), orchestrator (Python), and Claude Code (headless mode). Has
  draft-only permissions. Pushes to GitHub.

- **Local Agent**: The AI Employee instance running on the owner's laptop (WSL). Has full
  permissions including send/publish/approve. Pulls from GitHub. Manages sensitive
  credentials and Dashboard.md.

- **Synced Vault**: A Git repository directory shared between Cloud and Local agents via
  GitHub. Contains task files, draft files, approval files, status updates, and logs.
  Excludes sensitive data via `.gitignore`.

- **Vault Folder Structure**: Organized hierarchy (`/Needs_Action/`, `/In_Progress/`,
  `/Pending_Approval/`, `/Updates/`, `/Done/`, `/Logs/`) that encodes task state through
  file location rather than file content.

- **Claim-by-Move**: Concurrency control mechanism where file movement from `/Needs_Action/`
  to `/In_Progress/<agent>/` constitutes task ownership. First mover wins.

- **Health Monitor**: Script running on Cloud VM that periodically checks all components
  (Odoo, watchers, orchestrator, disk, RAM) and triggers auto-restart or alerts on failure.

- **Draft File**: Markdown file created by Cloud Agent containing a proposed action (email
  reply, social post, invoice) awaiting owner approval. Located in `/Pending_Approval/`.

- **Approval Flow**: The process by which a Cloud-created draft moves through the vault:
  created in `/Pending_Approval/` → synced via Git → reviewed by owner on Local →
  approved or rejected → executed or archived → moved to `/Done/`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Platinum Demo completes end-to-end (email → cloud draft → sync → local
  approve → send) with laptop OFF during email receipt — verified by executing the
  demo 3 times with different email types.

- **SC-002**: Cloud VM runs continuously for 48+ hours without manual intervention —
  verified by uptime check and activity logs showing overnight email processing.

- **SC-003**: Git sync delivers vault changes from Cloud to Local within 5 minutes
  (2-3 min pull interval + push delay) — verified with 10 timed sync operations.

- **SC-004**: Cloud Agent NEVER invokes send/publish MCP tools — verified by auditing
  all Cloud Agent actions in logs over a 24-hour period (zero send/publish entries).

- **SC-005**: Local Agent auto-starts within 60 seconds of laptop login without manual
  intervention — verified on 3 separate cold boots.

- **SC-006**: Health monitor detects and auto-restarts a crashed component within 5
  minutes — verified by manually killing each service and timing recovery.

- **SC-007**: Odoo is accessible via HTTPS with valid SSL certificate from both Cloud
  Agent and external browser — verified with `curl -I https://...` and browser check.

- **SC-008**: `.gitignore` prevents ALL sensitive files from being synced — verified by
  running `git log --all --diff-filter=A --name-only` and confirming zero sensitive
  file paths in history.

- **SC-009**: Claim-by-move prevents duplicate task processing — verified by creating
  a race condition (both agents check `/Needs_Action/` within seconds) and confirming
  only one agent processes the task.

- **SC-010**: Vault sync handles 24+ hours of laptop-off accumulation — verified by
  leaving laptop off for 24 hours, then confirming all Cloud-created drafts arrive
  on Local in correct chronological order.

---

## Assumptions

- Gold tier is fully implemented and functional before Platinum tier begins.
- The owner has an Oracle Cloud Free Tier account (or can create one — free).
- The owner has a domain name or will use the VM's public IP for Odoo HTTPS
  (Let's Encrypt requires a domain for automatic certificates; IP-only setups use
  self-signed certificates).
- The owner has a GitHub account with SSH key access for Git sync.
- The Anthropic API key (for Claude Code) is available for both Cloud and Local
  environments (same key can be used, or separate keys).
- Oracle Cloud Free Tier ARM A1 (4 OCPUs, 24GB RAM) is available in the owner's
  region (availability varies; may need to retry or use a different region).
- The owner's laptop runs Windows with WSL2 (Ubuntu) — consistent with existing setup.
- Claude Code CLI supports headless mode (`claude -p`) on ARM64 Linux (Ubuntu on ARM A1).
- Network connectivity is generally stable; brief outages are handled by retry logic.
- All Gold tier MCP servers (fte-email, fte-facebook, fte-instagram, fte-odoo) work
  without modification except for URL changes (local → cloud for Odoo).

---

## Out of Scope (Platinum Tier)

- A2A (Agent-to-Agent) direct messaging protocol — SKIPPED by decision (file-based sufficient)
- Custom domain purchase or DNS management beyond what's needed for HTTPS
- Multi-tenant or multi-user support (single owner only)
- Mobile app notifications (vault-based notifications only)
- Kubernetes or container orchestration (single VM deployment)
- Load balancing or horizontal scaling
- Paid cloud services beyond Oracle Free Tier
- Automated Odoo configuration (owner does initial setup via web UI)
- Voice/video processing on cloud
- Real-time collaboration between Cloud and Local (async via Git is the design choice)

---

## Pre-Implementation Setup Required

Before implementation begins, the owner must complete these setup steps:

1. **Oracle Cloud Account**: Sign up for Oracle Cloud Free Tier (free, requires credit card
   for verification but no charge)
2. **Provision VM**: Create an ARM A1 Compute instance (4 OCPUs, 24GB RAM, Ubuntu 22.04+)
3. **SSH Key**: Generate SSH key pair and configure key-only access to the VM
4. **GitHub Repo**: Create a private GitHub repository for vault sync
5. **SSH Keys on VM**: Add GitHub SSH key to the VM for passwordless git push/pull
6. **Domain (Optional)**: Point a domain to the VM's public IP for Odoo HTTPS with Let's
   Encrypt (alternative: self-signed certificate with VM IP)
7. **Anthropic API Key**: Ensure API key is available for Claude Code on the cloud VM
8. **Local WSL**: Verify Windows Task Scheduler can trigger WSL commands on login

---

## Dependency Chain

```
Gold Tier (complete)
    └── Platinum Tier
        ├── Oracle Cloud VM Setup (P2) ──────────────────┐
        │   └── Install Python, uv, Claude Code CLI      │
        │   └── Configure PM2/systemd                     │
        │   └── SSH security (key-only, fail2ban)         │
        ├── Vault Sync Setup (P4) ───────────────────────┤── Requires VM + GitHub repo
        │   └── .gitignore security rules (P5) ──────────┤── MUST be BEFORE first sync
        │   └── Folder structure creation                 │
        │   └── Hybrid sync (gitwatch + cron pull)        │
        ├── Work-Zone Specialization (P3) ───────────────┤── Requires Vault Sync
        │   └── Cloud Agent draft-only config             │
        │   └── Local Agent approval config               │
        │   └── Single-writer Dashboard rule              │
        ├── Odoo on Cloud (P6) ──────────────────────────┤── Requires VM
        │   └── Docker + Nginx + certbot                  │
        │   └── MCP server URL update                     │
        │   └── Backup + health monitoring                │
        ├── Health Monitoring (P7) ──────────────────────┤── Requires all services running
        ├── Local Auto-Start (P8) ──────────────────────┤── Independent (Local-side only)
        └── Platinum Demo (P1) ──────────────────────────┘── Requires ALL above working
```

Note: P1 (Platinum Demo) is the highest *priority* but depends on all other stories.
Implementation order follows the dependency chain: P2 → P5 → P4 → P3 → P6 → P7 → P8 → P1.

---

## Migration from Gold Tier

| Component | Gold Tier (Current) | Platinum Tier (Target) | Migration Action |
|-----------|-------------------|----------------------|------------------|
| Odoo | Local Docker (`localhost:8069`) | Cloud Docker (HTTPS) | Redeploy on VM, update MCP URL |
| Email Watcher | Local Python script | Cloud Python script | Deploy same script on VM |
| Social Watchers | Local Python scripts | Cloud Python scripts | Deploy same scripts on VM |
| Orchestrator | Local Python script | Cloud + Local orchestrators | Split into cloud-orchestrator and local-orchestrator |
| MCP Servers | All local | Split: read-only on Cloud, full on Local | Configure separate MCP permissions |
| Dashboard.md | Claude writes directly | Local Agent only (single-writer) | Add write restriction logic |
| Credentials | Single `.env` | Cloud `.env` (limited) + Local `.env` (full) | Split credentials by zone |
| Process Mgmt | Manual start | PM2/systemd (Cloud) + Task Scheduler (Local) | Configure auto-start on both |
