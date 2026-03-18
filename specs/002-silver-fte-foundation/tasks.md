# Tasks: Silver Tier — Functional Assistant

**Input**: Design documents from `/specs/002-silver-fte-foundation/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested — implementation tasks only.

**Organization**: Tasks grouped by user story (8 stories: P1-P8) for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US8)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install Silver tier dependencies and create directory structure

- [ ] T001 Install Silver tier Python dependencies via uv in pyproject.toml
- [ ] T002 [P] Install Playwright and download Chromium browser via `playwright install chromium`
- [ ] T003 [P] Create .secrets/ directory for OAuth credentials (add to .gitignore)
- [ ] T004 [P] Create .sessions/ directory for Playwright persistent contexts (add to .gitignore)
- [ ] T005 [P] Create .state/ directory for watcher runtime status (add to .gitignore)
- [ ] T006 [P] Create config/ directory for schedule and keyword configuration
- [ ] T007 [P] Create AI_Employee_Vault/Plans/ directory for reasoning scratchpads
- [ ] T008 [P] Create src/mcp/ directory for MCP server code
- [ ] T009 [P] Create src/automation/ directory for LinkedIn poster
- [ ] T010 Update .gitignore with .secrets/, .sessions/, .state/, jobs.db

**Checkpoint**: Silver tier project structure ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 Extend src/watchers/base_watcher.py with status reporting interface in src/watchers/base_watcher.py
- [ ] T012 Create watcher status manager in src/utils/watcher_status.py (reads/writes .state/watchers.json)
- [ ] T013 [P] Create config/keywords.json with default WhatsApp keywords list
- [ ] T014 [P] Create config/schedules.json with default schedule definitions
- [ ] T015 Extend src/utils/logger.py with platform-specific log fields (platform, message_id)
- [ ] T016 [P] Create .env.example with Silver tier environment variables (GMAIL_CREDENTIALS_PATH, etc.)

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Gmail Watcher Detects Emails (Priority: P1)

**Goal**: Gmail Watcher authenticates via OAuth2 and creates EMAIL_*.md action files for important unread emails

**Independent Test**: Send test email marked important → Within 2 minutes, EMAIL_{id}.md appears in Needs_Action/

### Implementation for User Story 1

- [ ] T017 [US1] Create Gmail OAuth2 authentication helper in src/watchers/gmail_auth.py
- [ ] T018 [US1] Implement first-time authorization flow with browser consent in src/watchers/gmail_auth.py
- [ ] T019 [US1] Implement automatic token refresh logic in src/watchers/gmail_auth.py
- [ ] T020 [US1] Create GmailWatcher class extending BaseWatcher in src/watchers/gmail_watcher.py
- [ ] T021 [US1] Implement check_for_updates() with Gmail API query 'is:unread is:important' in src/watchers/gmail_watcher.py
- [ ] T022 [US1] Implement email parsing (sender, subject, body snippet, labels) in src/watchers/gmail_watcher.py
- [ ] T023 [US1] Implement EMAIL_{message_id}.md creation with YAML frontmatter in src/watchers/gmail_watcher.py
- [ ] T024 [US1] Implement mark-as-read after processing in src/watchers/gmail_watcher.py
- [ ] T025 [US1] Add --authorize and --once CLI flags for setup/testing in src/watchers/gmail_watcher.py
- [ ] T026 [US1] Update watcher status in .state/watchers.json after each check in src/watchers/gmail_watcher.py
- [ ] T027 [US1] Create email_responder.md Agent Skill in .claude/skills/email_responder.md

**Checkpoint**: Gmail Watcher independently functional — test with real email

---

## Phase 4: User Story 2 — Human-in-the-Loop Approval Workflow (Priority: P2)

**Goal**: Sensitive actions create approval files in Pending_Approval/, orchestrator watches Approved/ folder and executes

**Independent Test**: Create approval file → Move to Approved/ → Action executes within 60 seconds

### Implementation for User Story 2

- [ ] T028 [US2] Create ApprovalManager class in src/orchestrator/approval_manager.py
- [ ] T029 [US2] Implement create_approval_request() with ACTION_{type}_{id}_{date}.md format in src/orchestrator/approval_manager.py
- [ ] T030 [US2] Implement watch_approved_folder() using watchdog in src/orchestrator/approval_manager.py
- [ ] T031 [US2] Implement execute_approved_action() dispatcher in src/orchestrator/approval_manager.py
- [ ] T032 [US2] Implement handle_rejection() logging in src/orchestrator/approval_manager.py
- [ ] T033 [US2] Extend orchestrator.py to integrate ApprovalManager in src/orchestrator/orchestrator.py
- [ ] T034 [US2] Update Company_Handbook.md with Silver tier approval rules in AI_Employee_Vault/Company_Handbook.md
- [ ] T035 [US2] Create approval_checker.md Agent Skill in .claude/skills/approval_checker.md

**Checkpoint**: Approval workflow independently functional — test with mock action file

---

## Phase 5: User Story 3 — WhatsApp Watcher via Playwright (Priority: P3)

**Goal**: WhatsApp Watcher monitors WhatsApp Web for keyword messages and creates WA_*.md action files

**Independent Test**: Send WhatsApp message with "urgent" → Within 2 minutes, WA_*.md appears in Needs_Action/

### Implementation for User Story 3

- [ ] T036 [US3] Create WhatsAppWatcher class extending BaseWatcher in src/watchers/whatsapp_watcher.py
- [ ] T037 [US3] Implement launch_persistent_context() for session persistence in src/watchers/whatsapp_watcher.py
- [ ] T038 [US3] Implement WhatsApp Web navigation and login detection in src/watchers/whatsapp_watcher.py
- [ ] T039 [US3] Implement unread message detection via DOM selectors in src/watchers/whatsapp_watcher.py
- [ ] T040 [US3] Implement keyword filtering from config/keywords.json in src/watchers/whatsapp_watcher.py
- [ ] T041 [US3] Implement WA_{sender}_{timestamp}.md creation with YAML frontmatter in src/watchers/whatsapp_watcher.py
- [ ] T042 [US3] Implement session expiration detection and notification file creation in src/watchers/whatsapp_watcher.py
- [ ] T043 [US3] Add --setup and --once CLI flags for initial QR scan and testing in src/watchers/whatsapp_watcher.py
- [ ] T044 [US3] Update watcher status in .state/watchers.json after each check in src/watchers/whatsapp_watcher.py
- [ ] T045 [US3] Create whatsapp_handler.md Agent Skill in .claude/skills/whatsapp_handler.md

**Checkpoint**: WhatsApp Watcher independently functional — test with keyword message

---

## Phase 6: User Story 4 — Claude Reasoning Loop Creates Plan.md (Priority: P4)

**Goal**: Claude creates PLAN_{task}_{date}.md with checkbox steps for complex multi-step tasks

**Independent Test**: Request complex task → PLAN_*.md created in Plans/ with logical steps

### Implementation for User Story 4

- [ ] T046 [US4] Create PlanManager class in src/utils/plan_manager.py
- [ ] T047 [US4] Implement create_plan() with PLAN_{slug}_{date}.md format in src/utils/plan_manager.py
- [ ] T048 [US4] Implement add_step() with markdown checkbox format in src/utils/plan_manager.py
- [ ] T049 [US4] Implement mark_step_complete() with timestamp in src/utils/plan_manager.py
- [ ] T050 [US4] Implement get_next_step() for sequential execution in src/utils/plan_manager.py
- [ ] T051 [US4] Implement detect_approval_required() for steps needing HITL in src/utils/plan_manager.py
- [ ] T052 [US4] Create plan_creator.md Agent Skill with step decomposition logic in .claude/skills/plan_creator.md

**Checkpoint**: Plan.md creation independently functional — test with multi-step request

---

## Phase 7: User Story 5 — Email MCP Server Sends Emails (Priority: P5)

**Goal**: MCP server exposes send_email tool that Claude can invoke to send approved emails

**Independent Test**: Approve email action → Email sent via MCP → Recipient receives email

**Dependencies**: Requires US1 (Gmail auth) and US2 (Approval workflow)

### Implementation for User Story 5

- [ ] T053 [US5] Create MCP server entry point in src/mcp/email_server.py
- [ ] T054 [US5] Implement MCP server initialization with mcp package in src/mcp/email_server.py
- [ ] T055 [US5] Implement send_email tool with to, subject, body, attachment params in src/mcp/email_server.py
- [ ] T056 [US5] Implement Gmail API send via google-api-python-client in src/mcp/email_server.py
- [ ] T057 [US5] Implement draft_email tool for creating drafts in src/mcp/email_server.py
- [ ] T058 [US5] Implement error handling and retry logic (max 3 attempts) in src/mcp/email_server.py
- [ ] T059 [US5] Create MCP configuration file template at config/mcp.json.example
- [ ] T060 [US5] Document MCP setup in quickstart.md (already exists, verify accuracy)

**Checkpoint**: MCP email server independently functional — test send with Claude Code

---

## Phase 8: User Story 6 — LinkedIn Auto-Post via Playwright (Priority: P6)

**Goal**: Playwright automates LinkedIn posting after approval, with stealth mode to avoid detection

**Independent Test**: Approve LinkedIn post → Post published on LinkedIn within 5 minutes

**Dependencies**: Requires US2 (Approval workflow)

### Implementation for User Story 6

- [ ] T061 [US6] Create LinkedInPoster class in src/automation/linkedin_poster.py
- [ ] T062 [US6] Implement launch_persistent_context() with stealth mode in src/automation/linkedin_poster.py
- [ ] T063 [US6] Implement LinkedIn login detection and handling in src/automation/linkedin_poster.py
- [ ] T064 [US6] Implement random delays between actions (2-5 seconds) in src/automation/linkedin_poster.py
- [ ] T065 [US6] Implement post creation flow (click "Start a post", enter text, click Post) in src/automation/linkedin_poster.py
- [ ] T066 [US6] Implement CAPTCHA/bot detection and notification file creation in src/automation/linkedin_poster.py
- [ ] T067 [US6] Implement post URL capture for logging in src/automation/linkedin_poster.py
- [ ] T068 [US6] Add --setup CLI flag for initial login in src/automation/linkedin_poster.py
- [ ] T069 [US6] Create linkedin_poster.md Agent Skill for content generation in .claude/skills/linkedin_poster.md

**Checkpoint**: LinkedIn posting independently functional — test with approved post

---

## Phase 9: User Story 7 — Basic Scheduling via APScheduler (Priority: P7)

**Goal**: APScheduler runs tasks at configured times with SQLite persistence

**Independent Test**: Schedule task for 5 minutes → Task executes at scheduled time

### Implementation for User Story 7

- [ ] T070 [US7] Create Scheduler class with APScheduler in src/orchestrator/scheduler.py
- [ ] T071 [US7] Configure SQLite jobstore for persistence (jobs.db) in src/orchestrator/scheduler.py
- [ ] T072 [US7] Implement load_schedules() from config/schedules.json in src/orchestrator/scheduler.py
- [ ] T073 [US7] Implement add_job() with cron and interval trigger support in src/orchestrator/scheduler.py
- [ ] T074 [US7] Implement remove_job() and update_job() for dynamic changes in src/orchestrator/scheduler.py
- [ ] T075 [US7] Implement job execution logging with timestamp and result in src/orchestrator/scheduler.py
- [ ] T076 [US7] Integrate scheduler into main.py startup in src/main.py
- [ ] T077 [US7] Create default schedules in config/schedules.json (Gmail 9AM, WhatsApp every 30min)

**Checkpoint**: Scheduler independently functional — test with 1-minute scheduled task

---

## Phase 10: User Story 8 — Enhanced Dashboard with Watcher Status (Priority: P8)

**Goal**: Dashboard.md shows watcher status, pending approvals, and platform statistics

**Independent Test**: Dashboard.md accurately reflects system state within 2 minutes of changes

### Implementation for User Story 8

- [ ] T078 [US8] Create DashboardManager class in src/utils/dashboard.py
- [ ] T079 [US8] Implement get_watcher_status_table() from .state/watchers.json in src/utils/dashboard.py
- [ ] T080 [US8] Implement get_pending_approvals_count() from Pending_Approval/ in src/utils/dashboard.py
- [ ] T081 [US8] Implement get_platform_stats() from Logs/ in src/utils/dashboard.py
- [ ] T082 [US8] Implement get_scheduled_tasks() from scheduler in src/utils/dashboard.py
- [ ] T083 [US8] Implement update_dashboard() to render all sections in src/utils/dashboard.py
- [ ] T084 [US8] Update Dashboard.md template with Silver tier sections in AI_Employee_Vault/Dashboard.md
- [ ] T085 [US8] Extend update_dashboard.md Agent Skill with Silver sections in .claude/skills/update_dashboard.md

**Checkpoint**: Dashboard independently functional — verify accuracy after actions

---

## Phase 11: Polish & Integration

**Purpose**: Final integration, PM2 configuration, and validation

- [ ] T086 Update src/main.py to start all watchers and scheduler in src/main.py
- [ ] T087 [P] Update ecosystem.config.js with Silver tier processes (gmail-watcher, whatsapp-watcher)
- [ ] T088 [P] Update .env.example with all Silver tier environment variables
- [ ] T089 Run quickstart.md validation — verify all setup steps work
- [ ] T090 Test end-to-end: Gmail → Action File → Claude → Approval → MCP Send
- [ ] T091 Test end-to-end: WhatsApp keyword → Action File → Claude → Response
- [ ] T092 Test scheduled task execution across system restart
- [ ] T093 Verify Dashboard accuracy after 10+ actions

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → User Stories (Phases 3-10) → Phase 11 (Polish)
```

### User Story Dependencies

| Story | Can Start After | Dependencies |
|-------|-----------------|--------------|
| US1 (Gmail) | Phase 2 | None |
| US2 (Approval) | Phase 2 | None |
| US3 (WhatsApp) | Phase 2 | None |
| US4 (Plan.md) | Phase 2 | None |
| US5 (MCP Email) | Phase 2 | US1 (Gmail auth), US2 (Approval) |
| US6 (LinkedIn) | Phase 2 | US2 (Approval) |
| US7 (Scheduler) | Phase 2 | None |
| US8 (Dashboard) | Phase 2 | None (reads status from other watchers) |

### Parallel Opportunities

After Phase 2 completion, these stories can run in parallel:
- US1 (Gmail) + US2 (Approval) + US3 (WhatsApp) + US4 (Plan.md) + US7 (Scheduler) + US8 (Dashboard)

After US1 + US2 complete:
- US5 (MCP Email) can start

After US2 completes:
- US6 (LinkedIn) can start

---

## Summary

| Phase | Story | Task Count | Parallel Tasks |
|-------|-------|------------|----------------|
| 1 | Setup | 10 | 7 |
| 2 | Foundational | 6 | 3 |
| 3 | US1 Gmail | 11 | 0 |
| 4 | US2 Approval | 8 | 0 |
| 5 | US3 WhatsApp | 10 | 0 |
| 6 | US4 Plan.md | 7 | 0 |
| 7 | US5 MCP Email | 8 | 0 |
| 8 | US6 LinkedIn | 9 | 0 |
| 9 | US7 Scheduler | 8 | 0 |
| 10 | US8 Dashboard | 8 | 0 |
| 11 | Polish | 8 | 2 |
| **Total** | | **93** | **12** |

---

## Implementation Strategy

### MVP First (US1 + US2 + US3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete US1: Gmail Watcher → Test independently
4. Complete US2: Approval Workflow → Test independently
5. Complete US3: WhatsApp Watcher → Test independently
6. **STOP and VALIDATE**: Three watchers working with approval

### Incremental Delivery

1. MVP (US1 + US2 + US3) → Demo: Email + WhatsApp monitoring with approval
2. Add US4 (Plan.md) → Demo: Complex task reasoning
3. Add US5 (MCP Email) → Demo: Approved email sending
4. Add US6 (LinkedIn) → Demo: Approved LinkedIn posting
5. Add US7 (Scheduler) → Demo: Automated task scheduling
6. Add US8 (Dashboard) → Demo: System health visibility

### Estimated Effort

Based on hackathon documentation (20-30 hours for Silver tier):
- Phase 1-2: ~2 hours
- US1-US4: ~10 hours (core functionality)
- US5-US6: ~8 hours (external actions)
- US7-US8: ~6 hours (scheduling + dashboard)
- Phase 11: ~4 hours (integration + testing)
