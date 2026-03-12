# Tasks: Platinum Tier — Always-On Cloud + Local Executive

**Input**: Design documents from `/specs/004-platinum-cloud-local/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Manual end-to-end verification at each checkpoint (no automated test tasks — testing is manual per spec).

**Organization**: Tasks follow the dependency chain: Setup → Security → Vault Sync → Zone Split → Odoo Cloud → Health → Auto-Start → Platinum Demo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US2, US3...)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create config files, directory structure, and shared modules needed by all user stories.

- [x] T001 Create vault folder structure per data-model.md in vault/ directory (Needs_Action/{email,social,invoice,general}, In_Progress/{cloud,local}, Plans/{email,social,invoice}, Pending_Approval/{email,social,invoice}, Updates/, Done/{email,social,invoice}, Logs/, Briefings/)
- [x] T002 [P] Create cloud agent config file at config/cloud-agent.yaml with draft-only zone permissions and model_config (sonnet/opus/ollama) per data-model.md
- [x] T003 [P] Create local agent config file at config/local-agent.yaml with full-access zone permissions and model_config per data-model.md
- [x] T004 [P] Create PM2 ecosystem config at config/ecosystem.config.js defining processes: email-watcher, orchestrator, health-monitor, gitwatch per data-model.md
- [x] T005 [P] Create Nginx reverse proxy config at config/nginx-odoo.conf with proxy_pass to localhost:8069 and SSL placeholder per quickstart.md Phase 3
- [x] T006 Implement model_selector.py in src/orchestrator/model_selector.py — load agent config YAML, assess task complexity (routine vs complex), select model (sonnet-4-6 / opus-4-6 / ollama minimax:m2.5:cloud), check API quota, return model string per contracts/cloud-local-protocol.md Model Selection protocol

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core modules that MUST be complete before any user story — vault management and git sync.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Implement vault_manager.py in src/orchestrator/vault_manager.py — functions: create_task_file() with YAML frontmatter per data-model.md Task File entity, move_task() for state transitions, claim_task() implementing claim-by-move (move from Needs_Action to In_Progress/<agent>), list_tasks_by_folder(), read_task_frontmatter(), write_status_update() to Updates/ folder
- [x] T008 Implement git_sync.py in src/sync/git_sync.py — functions: git_push() with auto-commit message "auto: <agent> <timestamp>", git_pull_rebase() with conflict resolution per contracts/ Conflict Resolution table (theirs for task files, ours for Dashboard.md, concat for logs), check_sync_status() returning last push/pull timestamps, is_github_reachable()

**Checkpoint**: vault_manager and git_sync modules ready — user story implementation can begin.

---

## Phase 3: User Story 2 — Cloud 24/7 Deployment (Priority: P2)

**Goal**: AI Employee system deployed on Oracle Cloud ARM A1 VM running 24/7 with auto-restart.

**Independent Test**: SSH into VM, verify all processes running via `pm2 status`, run `claude -p "hello"`, reboot VM and verify auto-restart.

### Implementation for User Story 2

- [x] T009 [US2] Create setup-cloud-vm.sh in scripts/setup-cloud-vm.sh — automated provisioning script that installs: apt updates, git, curl, inotify-tools, fail2ban, nginx, Docker (docker.io docker-compose-v2), Node.js 22 LTS (nodesource), PM2 (npm global), uv (astral.sh), claude-agent-sdk (pip), and configures SSH key-only auth (PasswordAuthentication no) per research.md R-003 and quickstart.md Phase 1
- [x] T010 [US2] Create start-cloud.sh in scripts/start-cloud.sh — startup script that: loads .env, starts PM2 with ecosystem.config.js, starts gitwatch pointing to vault path with -r origin -b main, sets up cron pull (*/3 * * * * cd $VAULT_PATH && git pull --rebase), logs startup to /var/log/fte-cloud-start.log
- [x] T011 [US2] Implement cloud_orchestrator.py in src/orchestrator/cloud_orchestrator.py — extends existing orchestrator.py, loads cloud-agent.yaml config, polls Needs_Action/ folders, claims tasks via vault_manager.claim_task("cloud"), invokes Claude Code via claude-agent-sdk (query() for routine, ClaudeSDKClient for complex) using model from model_selector, creates draft files in Pending_Approval/, writes status updates to Updates/ per cloud-local-protocol.md, enforces forbidden_actions list (raises error if send/publish attempted)
- [x] T012 [US2] Create cloud_orchestrator.md Agent Skill in .claude/skills/cloud_orchestrator.md — defines Cloud Agent behavior: draft-only zone, allowed/forbidden actions, model selection rules, vault protocol, status update frequency (every 30 min or after batch)
- [x] T013 [US2] Configure PM2 startup persistence — document in scripts/setup-cloud-vm.sh the commands: `pm2 start config/ecosystem.config.js`, `pm2 save`, `pm2 startup` to survive VM reboots per research.md R-005

**Checkpoint**: Cloud VM running 24/7, all services managed by PM2, Claude Code accessible via headless mode.

---

## Phase 4: User Story 5 — Security: Vault Sync Excludes Sensitive Data (Priority: P5)

**Goal**: .gitignore configured BEFORE first sync to prevent any sensitive file from entering Git history.

**Independent Test**: Run `git add .env` in vault — must be rejected. Push vault to GitHub, verify zero sensitive files in remote.

### Implementation for User Story 5

- [x] T014 [US5] Create vault .gitignore at vault/.gitignore — exclude patterns per spec.md FR-014: .env, *.token, *.session, *credentials*, *.key, *.pem, whatsapp-session/, banking/, *secret*, *.pickle, *.p12, .DS_Store, *.swp, .vscode/ — MUST be committed BEFORE any other vault content
- [x] T015 [P] [US5] Create cloud .env template at config/cloud.env.example — document all required Cloud VM environment variables per data-model.md Credential Split (ANTHROPIC_API_KEY, GMAIL_CREDENTIALS_PATH, META tokens, ODOO connection, GITHUB_SSH_KEY, VAULT_PATH) with placeholder values and comments explaining each
- [x] T016 [P] [US5] Create local .env template at config/local.env.example — document all Local environment variables (everything in cloud.env.example PLUS WHATSAPP_SESSION_PATH, BANKING_CREDENTIALS, PERSONAL_API_TOKENS) per data-model.md
- [x] T017 [US5] Add vault security validation function to src/sync/git_sync.py — validate_vault_security() that scans git staging area before push, rejects if any file matches sensitive patterns (.env, *.token, etc.), logs rejection, returns bool

**Checkpoint**: Vault security hardened — no sensitive data can accidentally be pushed to GitHub.

---

## Phase 5: User Story 4 — Git-Synced Vault with Claim-by-Move (Priority: P4)

**Goal**: Bidirectional Git sync between Cloud and Local via GitHub with claim-by-move conflict resolution.

**Independent Test**: Create file in vault on Cloud, verify it appears on Local within 3 minutes. Move file to In_Progress/cloud/ on Cloud, verify Local sees the move.

### Implementation for User Story 4

- [x] T018 [US4] Configure gitwatch on Cloud — add to scripts/start-cloud.sh: install gitwatch from github.com/gitwatch/gitwatch, run `gitwatch -r origin -b main $VAULT_PATH` as PM2 managed process in ecosystem.config.js per research.md R-002
- [x] T019 [US4] Configure cron git pull on Cloud — add to scripts/start-cloud.sh: crontab entry `*/3 * * * * cd $VAULT_PATH && git pull --rebase origin main >> /var/log/git-pull.log 2>&1` per research.md R-002
- [x] T020 [P] [US4] Configure gitwatch on Local — create scripts/setup-local-sync.sh that installs inotify-tools, clones gitwatch, installs it, and starts `gitwatch -r origin -b main $VAULT_PATH` for WSL environment
- [x] T021 [P] [US4] Configure cron git pull on Local — add to scripts/start-local.sh: crontab entry for WSL `*/3 * * * * cd $VAULT_PATH && git pull --rebase origin main >> ~/git-pull.log 2>&1`
- [x] T022 [US4] Implement claim-by-move conflict handling in src/sync/git_sync.py — extend git_pull_rebase() to detect merge conflicts, apply resolution strategy per contracts/ Conflict Resolution table, log all conflict resolutions, alert owner for unresolvable conflicts via vault Updates/ file
- [x] T023 [US4] Create vault_sync_manager.md Agent Skill in .claude/skills/vault_sync_manager.md — documents vault sync behavior, claim-by-move rules, conflict resolution strategies, gitwatch + cron setup, troubleshooting

**Checkpoint**: Bidirectional sync working — Cloud pushes, Local pulls (and vice versa) within 3 minutes.

---

## Phase 6: User Story 3 — Work-Zone Specialization (Priority: P3)

**Goal**: Cloud Agent restricted to drafts only. Local Agent handles all final actions and sensitive operations.

**Independent Test**: Cloud Agent attempts to call send_email_tool — must be blocked. Local Agent sends email after approval — must succeed.

### Implementation for User Story 3

- [x] T024 [US3] Implement zone enforcement in src/orchestrator/cloud_orchestrator.py — before any MCP tool invocation, check cloud-agent.yaml forbidden_actions list, raise ZoneViolationError if send/publish/confirm attempted, log the violation
- [x] T025 [US3] Implement local_orchestrator.py in src/orchestrator/local_orchestrator.py — extends existing orchestrator.py, loads local-agent.yaml config, on startup: git pull, scan Pending_Approval/ for items, present pending approvals to owner, on approval: execute final action via MCP (send_email_tool, create_page_post, etc.), move task to Done/, update Dashboard.md (single-writer), read Updates/ from Cloud and merge into Dashboard.md
- [x] T026 [US3] Create local_orchestrator.md Agent Skill in .claude/skills/local_orchestrator.md — defines Local Agent behavior: full-access zone, approval workflow, Dashboard.md single-writer rule, credential management, notification of pending approvals
- [x] T027 [US3] Update existing approval_handler.py in src/orchestrator/approval_handler.py — add support for Cloud-generated approval files (read YAML frontmatter from draft files in Pending_Approval/), present draft content to owner, handle approve/reject/edit actions, on approve: invoke appropriate MCP tool, on reject: move to Done with status:rejected
- [x] T028 [US3] Implement Dashboard.md single-writer logic in src/orchestrator/local_orchestrator.py — Local Agent reads all files from Updates/ folder, merges Cloud status updates into Dashboard.md, deletes processed Updates/ files, enforces that only local_orchestrator writes Dashboard.md

**Checkpoint**: Zone split enforced — Cloud drafts only, Local approves and executes. Dashboard.md written only by Local.

---

## Phase 7: User Story 6 — Odoo on Cloud VM with HTTPS (Priority: P6)

**Goal**: Odoo migrated from local Docker to Cloud VM with HTTPS, backups, and health monitoring.

**Independent Test**: Access `https://odoo.<domain>` in browser, create invoice via Odoo MCP pointing to cloud URL, verify HTTPS cert valid.

### Implementation for User Story 6

- [x] T029 [US6] Create Odoo docker-compose for ARM64 at config/docker-compose-odoo.yml — use official odoo:17 image (multi-arch, includes ARM64), PostgreSQL image, volume mounts for config (/etc/odoo), addons (/mnt/extra-addons), and filestore, expose port 8069 on localhost only (Nginx handles external), restart: unless-stopped per research.md R-004
- [x] T030 [US6] Add Odoo deployment to scripts/setup-cloud-vm.sh — copy docker-compose-odoo.yml to VM, docker compose up -d, verify Odoo responds on localhost:8069
- [x] T031 [US6] Configure Nginx + Let's Encrypt in scripts/setup-cloud-vm.sh — install nginx and certbot, copy config/nginx-odoo.conf to /etc/nginx/sites-available/, enable site, run certbot --nginx -d odoo.<domain> (or self-signed cert for IP-only setup), verify HTTPS access per research.md R-003
- [x] T032 [US6] Create backup-odoo.sh in scripts/backup-odoo.sh — daily cron job: pg_dump Odoo database to ~/backups/odoo_YYYYMMDD.sql, filestore tar backup, retain 7 daily + 4 weekly, log backup result, alert on failure per spec.md FR-021
- [x] T033 [US6] Update Odoo MCP server URL — modify src/mcp/odoo_server.py to read ODOO_URL from .env (already does), document in config/cloud.env.example that Cloud sets ODOO_URL=http://localhost:8069 (same VM) and Local sets ODOO_URL=https://odoo.<domain> (remote HTTPS) per contracts/ MCP URL Changes

**Checkpoint**: Odoo running 24/7 on cloud with HTTPS. MCP server works from both Cloud (localhost) and Local (HTTPS).

---

## Phase 8: User Story 7 — Health Monitoring and Auto-Recovery (Priority: P7)

**Goal**: Health monitor checks all Cloud components every 3-5 minutes, auto-restarts on failure, alerts on repeated failure.

**Independent Test**: Kill email-watcher process, verify health monitor restarts it within 5 minutes. Check disk usage alert at 85% threshold.

### Implementation for User Story 7

- [x] T034 [US7] Implement health_monitor.py in src/health/health_monitor.py — functions: check_odoo() via HTTP to localhost:8069, check_process(name) via pgrep, check_disk() via shutil.disk_usage, check_ram() via psutil, check_last_activity() via vault file timestamps, run_all_checks() returning HealthCheckResult per data-model.md Health Check Result entity
- [x] T035 [US7] Implement auto-restart logic in src/health/health_monitor.py — on component failure: attempt pm2 restart <process_name>, track restart_count per component, if 3 consecutive failures: create alert file in vault Updates/alert_<timestamp>.md (syncs to Local via git), log all restart attempts to /var/log/fte-health/
- [x] T036 [US7] Create health-monitor.sh in scripts/health-monitor.sh — wrapper script that runs health_monitor.py via uv, designed for cron execution every 5 minutes: `*/5 * * * * /home/ubuntu/fte-project/scripts/health-monitor.sh >> /var/log/fte-health/cron.log 2>&1`
- [x] T037 [US7] Add health monitor to PM2 ecosystem — update config/ecosystem.config.js to include health-monitor as a managed process with cron_restart: "*/5 * * * *" or as standalone cron job per research.md R-005

**Checkpoint**: Health monitor running, auto-restart working, alerts syncing to Local via vault.

---

## Phase 9: User Story 8 — Local Agent Auto-Start on Laptop Boot (Priority: P8)

**Goal**: Laptop ON = Local Orchestrator auto-starts in background, pulls vault, checks pending approvals.

**Independent Test**: Restart laptop, without opening terminal verify Local Orchestrator is running and has pulled latest vault.

### Implementation for User Story 8

- [x] T038 [US8] Create start-local.sh in scripts/start-local.sh — startup script: cd to vault, git pull --rebase origin main, cd to project, start local_orchestrator.py in background, start gitwatch for vault, start cron pull, log startup to ~/fte-local-start.log per quickstart.md Phase 5
- [x] T039 [US8] Create Windows Task Scheduler VBS launcher at scripts/start-local-hidden.vbs — VBScript that runs `wsl -d Ubuntu -- bash -c "/path/to/start-local.sh"` with hidden window (WScript.Shell.Run with 0 flag) so no terminal popup per research.md R-006
- [x] T040 [US8] Document Windows Task Scheduler setup in scripts/README-local-autostart.md — step-by-step: open Task Scheduler, create task "FTE Local Orchestrator", trigger "At log on", action run start-local-hidden.vbs, settings "Run whether user is logged on or not"
- [x] T041 [US8] Implement pending approval notification in src/orchestrator/local_orchestrator.py — on startup after git pull, count files in Pending_Approval/ subfolders, if > 0: log count, create notification file in vault, optionally update Dashboard.md with "X pending approvals from Cloud Agent"

**Checkpoint**: Laptop boot = Local Agent auto-running, vault synced, pending approvals visible.

---

## Phase 10: User Story 1 — Platinum Demo: End-to-End Email Flow (Priority: P1) MVP

**Goal**: Complete Platinum Demo — email arrives while laptop OFF → Cloud drafts → sync → Local approves → send → log → done.

**Independent Test**: Turn off laptop, send test email, wait for Cloud to draft, turn on laptop, approve, verify email sent and logged.

### Implementation for User Story 1

- [x] T042 [US1] Create Platinum Demo integration script at scripts/platinum-demo.sh — automated demo runner: 1) verify Cloud VM running (SSH health check), 2) verify Local orchestrator stopped, 3) trigger test email (or prompt user to send), 4) wait and poll Cloud vault for draft in Pending_Approval/email/, 5) prompt user to start Local, 6) verify Local pulls draft, 7) prompt approval, 8) verify email sent via MCP, 9) verify audit log entry, 10) verify task in Done/
- [x] T043 [US1] Create demo script document at docs/platinum-demo-script.md — step-by-step demo narration for hackathon judges per spec.md Platinum Demo section: what to show at each step, expected output, timing, talking points
- [x] T044 [US1] Implement end-to-end audit trail in src/orchestrator/cloud_orchestrator.py and local_orchestrator.py — each step of the Platinum Demo flow creates a JSON audit log entry with: step_number, timestamp, agent (cloud/local), action, input, output, duration_ms per spec.md FR-030. All entries share a workflow_id for the complete flow.
- [ ] T045 [US1] End-to-end verification — manually execute the Platinum Demo 3 times with different email types (quote request, meeting request, support question) per spec.md SC-001, verify each execution completes all 7 steps, review audit logs for completeness

**Checkpoint**: Platinum Demo works end-to-end. Minimum passing gate for Platinum Tier achieved!

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, hardening, and final improvements across all user stories.

- [x] T046 [P] Create architecture documentation at docs/platinum-architecture.md — system overview diagram (Cloud + Local + GitHub), component descriptions, data flow, vault protocol, zone permissions, model selection strategy
- [x] T047 [P] Create lessons-learned documentation at docs/platinum-lessons-learned.md — challenges encountered, solutions applied, recommendations for future development
- [x] T048 [P] Update existing .mcp.json to document Cloud vs Local MCP server configurations — add comments/documentation about which MCP tools are available on Cloud (read-only) vs Local (full access)
- [x] T049 Rate limiting for Cloud Agent — add to src/orchestrator/cloud_orchestrator.py: max 20 drafts/hour, max 10 emails/hour per spec.md Edge Cases (spam/flood protection)
- [ ] T050 Validate all requirements checklist — go through specs/004-platinum-cloud-local/checklists/requirements.md and verify each FR and SC checkbox

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──────────────────────────────────────────┐
Phase 2: Foundational (vault_manager, git_sync) ─────────┤ BLOCKS ALL
Phase 3: US2 Cloud VM Deployment ────────────────────────┤
Phase 4: US5 Security (.gitignore) ──────────────────────┤ BEFORE first sync!
Phase 5: US4 Vault Sync (gitwatch + cron) ───────────────┤ Requires Phase 3+4
Phase 6: US3 Work-Zone Split ────────────────────────────┤ Requires Phase 5
Phase 7: US6 Odoo on Cloud ─────────────────────────────┤ Requires Phase 3 (can parallel with 5,6)
Phase 8: US7 Health Monitoring ──────────────────────────┤ Requires Phase 3+7
Phase 9: US8 Local Auto-Start ──────────────────────────┤ Independent (can parallel with 7,8)
Phase 10: US1 Platinum Demo ─────────────────────────────┤ Requires ALL above
Phase 11: Polish ────────────────────────────────────────┘ After Phase 10
```

### User Story Dependencies

- **US2 (Cloud VM)**: Depends on Setup + Foundational — first to implement
- **US5 (Security)**: Depends on US2 (VM exists) — MUST be before US4
- **US4 (Vault Sync)**: Depends on US2 + US5 — sync needs VM + security
- **US3 (Zone Split)**: Depends on US4 — zone enforcement uses vault protocol
- **US6 (Odoo Cloud)**: Depends on US2 — can parallel with US4/US5
- **US7 (Health)**: Depends on US2 + US6 — monitors all cloud services
- **US8 (Auto-Start)**: Independent — Local-side only, can parallel with US6/US7
- **US1 (Platinum Demo)**: Depends on ALL — integration of everything

### Parallel Opportunities

```
After Phase 2 (Foundational):
  ├── US2 (Cloud VM) ── sequential, must be first
  │
After Phase 3 (Cloud VM ready):
  ├── US5 (Security) ── must be before US4
  ├── US6 (Odoo Cloud) ── can parallel with US5
  │
After Phase 4 (Security done):
  ├── US4 (Vault Sync) ── requires security
  │
After Phase 5 (Vault Sync working):
  ├── US3 (Zone Split)
  ├── US8 (Local Auto-Start) ── parallel with US3
  │
After Phase 6+7 (Zone + Odoo):
  ├── US7 (Health Monitor)
  │
After ALL:
  └── US1 (Platinum Demo)
```

---

## Parallel Example: Phase 1 Setup

```bash
# These 4 config files can be created simultaneously:
Task T002: "Create cloud-agent.yaml in config/"
Task T003: "Create local-agent.yaml in config/"
Task T004: "Create ecosystem.config.js in config/"
Task T005: "Create nginx-odoo.conf in config/"
```

## Parallel Example: After Cloud VM Ready

```bash
# US5 and US6 can run in parallel (different concerns):
Task T014: "[US5] Create vault .gitignore"
Task T029: "[US6] Create Odoo docker-compose for ARM64"
```

## Parallel Example: After Vault Sync Working

```bash
# US3 and US8 can run in parallel (different machines):
Task T024: "[US3] Implement zone enforcement (Cloud side)"
Task T038: "[US8] Create start-local.sh (Local side)"
```

---

## Implementation Strategy

### MVP First (Platinum Demo = US1)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T008)
3. Complete Phase 3: Cloud VM (T009-T013)
4. Complete Phase 4: Security (T014-T017)
5. Complete Phase 5: Vault Sync (T018-T023)
6. Complete Phase 6: Zone Split (T024-T028)
7. Complete Phase 7: Odoo Cloud (T029-T033)
8. Complete Phase 8: Health Monitor (T034-T037)
9. Complete Phase 9: Local Auto-Start (T038-T041)
10. Complete Phase 10: **Platinum Demo** (T042-T045) — **STOP and VALIDATE**
11. Complete Phase 11: Polish (T046-T050)

### Estimated Task Distribution

| Phase | Tasks | Parallel Opportunities |
|-------|-------|----------------------|
| Setup | T001-T006 (6) | T002-T005 parallel |
| Foundational | T007-T008 (2) | Sequential |
| US2 Cloud VM | T009-T013 (5) | Sequential |
| US5 Security | T014-T017 (4) | T015-T016 parallel |
| US4 Vault Sync | T018-T023 (6) | T020-T021 parallel |
| US3 Zone Split | T024-T028 (5) | Sequential |
| US6 Odoo Cloud | T029-T033 (5) | Sequential |
| US7 Health | T034-T037 (4) | Sequential |
| US8 Auto-Start | T038-T041 (4) | Sequential |
| US1 Demo | T042-T045 (4) | T042-T043 parallel |
| Polish | T046-T050 (5) | T046-T048 parallel |
| **TOTAL** | **50 tasks** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Pre-implementation setup (Oracle account, GitHub repo, SSH keys) is owner's manual work — not in task list
- All scripts include logging for debugging
- Each checkpoint = independently verifiable milestone
- Commit after each task or logical group
