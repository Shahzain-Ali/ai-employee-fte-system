# Tasks: Gold Tier — Autonomous Employee

**Input**: Design documents from `/specs/003-gold-fte-autonomous/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, research.md, quickstart.md

**Tests**: Not explicitly requested — test tasks are omitted. Each user story has independent test criteria for manual verification.

**Organization**: Tasks grouped by user story (spec.md priorities P1–P12) for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies, create directories, and prepare project for Gold tier

- [x] T001 Add `requests>=2.31.0` dependency via `uv add requests` in pyproject.toml
- [x] T002 [P] Create Gold tier vault directories: `AI_Employee_Vault/Briefings/`, `AI_Employee_Vault/Tasks/`
- [x] T003 [P] Create `scripts/` directory at project root and add to .gitignore exclusion
- [x] T004 [P] Create `src/scheduler/` package with `src/scheduler/__init__.py`
- [x] T005 [P] Create `.state/` directory for runtime health data and add to .gitignore

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Audit logging, error recovery, and component health — MUST complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Extend `src/utils/logger.py` LogEntry dataclass with new fields: `workflow_id` (str|None), `duration_ms` (int|None), `mcp_server` (str|None), `retry_count` (int|None), `error_message` (str|None), `domain` (str|None). Update `AuditLogger.log()` to include these in JSON output
- [x] T007 [P] Create `src/utils/audit_retention.py` — implement 90-day log retention policy: scan `vault/Logs/YYYY-MM-DD.json` files, archive/delete files older than configurable days (default: 90). Include disk usage check for Dashboard warning
- [x] T008 [P] Create `src/utils/retry.py` — implement `retry_with_backoff(max_retries=3, base_delay=1)` decorator for transient errors (ConnectionError, TimeoutError, rate limit). Exponential delays: 1s, 2s, 4s. Never retry payment/financial actions (check action_type)
- [x] T009 [P] Create `src/orchestrator/component_health.py` — implement ComponentHealthRegistry class: track status (healthy/degraded/down/unknown) for each domain (odoo, facebook, instagram, gmail, whatsapp). Methods: `update_health(domain, success: bool)`, `get_health(domain)`, `get_all_health()`. Store state in `.state/health.json`. Mark degraded after 1-2 failures, down after 3+

**Checkpoint**: Foundation ready — audit logging enhanced, retry utility available, health tracking active. User story implementation can now begin.

---

## Phase 3: User Story 1 — Odoo Accounting Integration (Priority: P1) MVP

**Goal**: Deploy Odoo via Docker and create custom MCP server for invoice/payment/expense management via JSON-RPC API

**Independent Test**: Start Odoo via docker-compose. Use the Odoo MCP server to create an invoice. Verify invoice appears in Odoo web interface at http://localhost:8069

### Implementation for User Story 1

- [x] T010 [US1] Create `config/docker-compose.yml` with Odoo 19 + PostgreSQL 16 services per research.md docker-compose template. Volumes: odoo-data, pg-data. Ports: 8069:8069. Environment from .env
- [x] T011 [US1] Add Odoo environment variables to `.env.example` (not .env itself): `ODOO_URL=http://localhost:8069`, `ODOO_DB=fte_gold`, `ODOO_USER=admin`, `ODOO_PASSWORD=changeme`
- [x] T012 [US1] Create `src/mcp/odoo_server.py` — Python MCP server using `mcp` SDK with stdio transport. Implement private `_odoo_jsonrpc(method, params)` helper using `requests` for JSON-RPC calls to `{ODOO_URL}/jsonrpc`. Load credentials from .env via `python-dotenv`. Implement 6 tools per contract `specs/003-gold-fte-autonomous/contracts/fte-odoo.md`: `create_invoice` (account.move with move_type=out_invoice), `get_invoices` (search_read with status filter), `mark_payment_received` (account.payment.register), `get_weekly_summary` (read_group on account.move.line), `get_expenses` (search_read on hr.expense), `create_expense` (create on hr.expense). All tool results returned as TextContent. Errors returned as TextContent (not thrown). Log to stderr only
- [x] T013 [US1] Register `fte-odoo` in `.mcp.json` — add entry: type=stdio, command=python, args=["src/mcp/odoo_server.py"], env={}
- [x] T014 [US1] Create `.claude/skills/odoo_accountant.md` — Agent Skill for Odoo operations: purpose, platform=odoo, inputs (action_file path), steps (read action, determine operation, invoke MCP tool, log result, create approval if payment), approval required for payments, output format, error handling instructions

**Checkpoint**: Odoo Docker running, MCP server operational. Test by creating invoice via Claude Code tool call → verify in Odoo web UI.

---

## Phase 4: User Story 2 — Facebook Business Page Integration (Priority: P2)

**Goal**: Custom MCP server for Facebook Page posting, comment management, and engagement insights via Meta Graph API

**Independent Test**: Create a test post on the Facebook Business Page via MCP server. Verify post appears on the Page. Get engagement summary.

### Implementation for User Story 2

- [x] T015 [P] Create `src/mcp/_meta_client.py` — shared Meta Graph API HTTP client class. Constructor takes `access_token`, `api_version` (default v21.0). Methods: `get(endpoint, params)`, `post(endpoint, data)`. Handle rate limit detection (check X-App-Usage header), token expiration (OAuthException error code 190), and return structured error messages. Use `retry_with_backoff` from `src/utils/retry.py` for transient errors. Log all API calls to stderr
- [x] T016 [US2] Create `src/mcp/facebook_server.py` — Python MCP server using `mcp` SDK with stdio transport. Import `MetaGraphClient` from `_meta_client.py`. Load `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN` from .env. Implement 5 tools per contract `specs/003-gold-fte-autonomous/contracts/fte-facebook.md`: `create_page_post` (POST /{page-id}/feed), `get_page_posts` (GET /{page-id}/feed with fields=message,created_time,likes.summary(true),comments.summary(true)), `get_post_comments` (GET /{post-id}/comments), `reply_to_comment` (POST /{comment-id}/comments), `get_page_insights` (GET /{page-id}/insights with page_views_total,page_post_engagements,page_fan_adds)
- [x] T017 [US2] Register `fte-facebook` in `.mcp.json` — add entry: type=stdio, command=python, args=["src/mcp/facebook_server.py"], env={}
- [x] T018 [US2] Create `.claude/skills/facebook_poster.md` — Agent Skill for Facebook operations: purpose, platform=facebook, inputs, steps (read action, compose post/reply, create approval request, wait for approval, invoke MCP tool, log result), approval required for ALL posts and replies, output format

**Checkpoint**: Facebook MCP server operational. Test by creating a post via Claude Code tool call → verify on Facebook Page.

---

## Phase 5: User Story 3 — Instagram Business Account Integration (Priority: P3)

**Goal**: Custom MCP server for Instagram content publishing (images, reels), comment management, and insights via Meta Graph API

**Independent Test**: Publish a test image with caption to Instagram via MCP server. Retrieve recent posts. Read comments.

### Implementation for User Story 3

- [x] T019 [US3] Create `src/mcp/instagram_server.py` — Python MCP server using `mcp` SDK with stdio transport. Import `MetaGraphClient` from `_meta_client.py`. Load `IG_USER_ID` and `IG_ACCESS_TOKEN` from .env. Implement 6 tools per contract `specs/003-gold-fte-autonomous/contracts/fte-instagram.md`: `create_ig_post` (2-step: POST /{ig-user-id}/media with image_url+caption → POST /{ig-user-id}/media_publish with creation_id), `create_ig_reel` (2-step with media_type=REELS and video_url), `get_ig_media` (GET /{ig-user-id}/media with fields=id,media_type,caption,timestamp,like_count,comments_count,permalink), `get_ig_comments` (GET /{media-id}/comments), `reply_ig_comment` (POST /{comment-id}/replies), `get_ig_insights` (GET /{ig-user-id}/insights with impressions,reach,profile_views). Check account type on startup — return clear error if not Business/Creator
- [x] T020 [US3] Register `fte-instagram` in `.mcp.json` — add entry: type=stdio, command=python, args=["src/mcp/instagram_server.py"], env={}
- [x] T021 [US3] Add Instagram environment variables to `.env.example`: `IG_USER_ID`, `IG_ACCESS_TOKEN`, `META_API_VERSION=v21.0`
- [x] T022 [US3] Create `.claude/skills/instagram_manager.md` — Agent Skill for Instagram operations: purpose, platform=instagram, inputs, steps (read action, compose caption, create approval request for posts/reels/replies, wait for approval, invoke MCP tool via 2-step container flow, log result), approval required for ALL publishing actions, daily limit tracking (25 posts/day), output format

**Checkpoint**: Instagram MCP server operational. Test by publishing image via Claude Code → verify on Instagram Business account.

---

## Phase 6: User Story 4 — Cross-Domain Integration (Priority: P4)

**Goal**: Connect Personal domain (Gmail, WhatsApp) with Business domain (Odoo, Facebook, Instagram) — single trigger cascades across domains

**Independent Test**: Send an email requesting an invoice. Verify AI creates Odoo invoice, sends email confirmation (after approval), and logs all actions with shared workflow_id.

**Dependencies**: Requires US1 (Odoo), US2 (Facebook), US3 (Instagram) complete

### Implementation for User Story 4

- [x] T023 [US4] Create `src/orchestrator/workflow_engine.py` — WorkflowEngine class: `start_workflow(trigger, steps)` generates unique workflow_id (uuid4), executes steps sequentially, tracks completed/failed/remaining. `_execute_step(step)` invokes appropriate MCP server. Handles partial failures: completed steps preserved, failed step logged with error, remaining steps noted. All actions logged with shared workflow_id. Creates notification file on failure. Returns workflow result object
- [x] T024 [US4] Extend `src/orchestrator/orchestrator.py` — add new action file prefixes to `_get_pending_files()`: `ODOO_`, `FB_`, `IG_`. Add routing in `_trigger_claude()`: ODOO_ → odoo_accountant skill, FB_ → facebook_poster skill, IG_ → instagram_manager skill. Add `_detect_cross_domain_trigger(action_file)` method: analyze content to detect if action should cascade (e.g., invoice request email → Odoo + email reply)
- [x] T025 [US4] Extend `src/orchestrator/approval_handler.py` — add approval type handlers for `facebook_post`, `facebook_reply`, `instagram_post`, `instagram_reel`, `instagram_reply`, `odoo_payment`. Each handler invokes appropriate MCP server tool upon approval. Pattern follows existing `_handle_email_send` and `_handle_whatsapp_reply`

**Checkpoint**: Cross-domain workflows operational. Test: email trigger → Odoo invoice + email reply → all logged with same workflow_id.

---

## Phase 7: User Story 5 — Weekly CEO Briefing Generation (Priority: P5)

**Goal**: Automated weekly report combining financial, social media, and communication data from all domains

**Independent Test**: Manually trigger CEO Briefing. Verify it pulls data from Odoo, Facebook, Instagram, Gmail (vault file counts), WhatsApp (vault file counts) and produces markdown report.

**Dependencies**: Requires US4 (all domains connected)

### Implementation for User Story 5

- [x] T026 [US5] Create `src/utils/ceo_briefing.py` — CEOBriefingGenerator class: `generate(week_start, week_end)` collects data from all domains. `_get_odoo_data()` calls fte-odoo get_weekly_summary (via direct JSON-RPC, not MCP). `_get_facebook_data()` calls Meta Graph API get_page_insights. `_get_instagram_data()` calls Meta Graph API get_ig_insights. `_get_communication_data()` counts EMAIL_/WA_ files in vault Done/ folder for the week. `_render_briefing(data)` generates markdown matching CEO Briefing template from data-model.md. Handles missing data sources gracefully — includes available data and notes unavailable. Saves to `vault/Briefings/CEO_Briefing_YYYY-MM-DD.md`. `_email_briefing(filepath)` optionally emails the generated briefing to the owner via fte-email MCP send_email_tool (reads OWNER_EMAIL from .env; skips if not configured)
- [x] T027 [US5] Create `src/scheduler/jobs.py` — define `register_gold_jobs(scheduler)` function: add CEO Briefing cron job (Sunday 22:00), add audit retention daily job (03:00). Import from `src/utils/ceo_briefing` and `src/utils/audit_retention`
- [x] T028 [US5] Update `config/schedules.json` — add CEO Briefing schedule entry: id=ceo_briefing_weekly, task=generate_ceo_briefing, cron="0 22 * * 0", description="Weekly CEO Briefing every Sunday at 10 PM"
- [x] T029 [US5] Create `.claude/skills/ceo_briefing.md` — Agent Skill: purpose (generate weekly business report), platform=general, inputs (week_start optional), steps (collect data from all domains, handle missing sources, generate markdown, save to Briefings/, optionally email to owner via email MCP), output format per data-model.md template

**Checkpoint**: CEO Briefing generator operational. Test: manual trigger → verify report has all sections with data from available domains.

---

## Phase 8: User Story 6 — Comprehensive Audit Logging (Priority: P6)

**Goal**: Every AI action logged in structured JSON with workflow tracking — already implemented in Phase 2 foundation. This phase adds the Agent Skill and query capability.

**Independent Test**: Trigger several actions (email, Odoo, Facebook). Verify each creates structured JSON log in vault/Logs/YYYY-MM-DD.json with all required fields.

**Note**: Core logging enhancement was done in T006. This phase adds skill + retention.

### Implementation for User Story 6

- [x] T030 [US6] Create `.claude/skills/audit_logger.md` — Agent Skill: purpose (structured logging of every AI action), platform=general, inputs (action details), steps (capture timestamp+action_type+actor+target+parameters+approval_status+result+duration_ms+mcp_server+workflow_id, sanitize sensitive data, write to Logs/YYYY-MM-DD.json, check retention policy), never log tokens/passwords/credit card numbers, output format per data-model.md
- [x] T031 [US6] Integrate audit logging into all MCP servers — add timing wrapper to each `call_tool()` handler in `src/mcp/odoo_server.py`, `src/mcp/facebook_server.py`, `src/mcp/instagram_server.py`. Calculate duration_ms, log action with mcp_server field. Import and use `AuditLogger` from `src/utils/logger.py`

**Checkpoint**: All MCP tool calls produce structured audit log entries. Verify by reviewing Logs/ after 20+ diverse actions.

---

## Phase 9: User Story 7 — Error Recovery and Graceful Degradation (Priority: P7)

**Goal**: System continues when components fail, retries transient errors, alerts owner on critical failures

**Independent Test**: Stop Odoo Docker while system runs. Verify email/WhatsApp processing continues, Odoo failure logged, operations resume when Docker restarts.

**Note**: Core retry utility was done in T008, health registry in T009. This phase integrates them.

### Implementation for User Story 7

- [x] T032 [US7] Integrate `retry_with_backoff` into all MCP servers — wrap API calls in `src/mcp/odoo_server.py` (JSON-RPC calls), `src/mcp/facebook_server.py` (Graph API calls), `src/mcp/instagram_server.py` (Graph API calls) with retry decorator. Update component health on success/failure via `ComponentHealthRegistry`
- [x] T033 [US7] Add notification file creation for critical failures — in `src/orchestrator/component_health.py`, when a component transitions to `down` status, create `NOTIFICATION_component_down_TIMESTAMP.md` in vault `Needs_Action/` with component name, error details, and suggested action
- [x] T034 [US7] Create `.claude/skills/error_handler.md` — Agent Skill: purpose (handle errors with retry, degradation, notifications), platform=general, inputs (error context), steps (classify error as transient/permanent, apply retry if transient, update health registry, create notification if critical, never auto-retry payments FR-026), escalation rules

**Checkpoint**: System gracefully handles component failures. Test: stop Odoo Docker → verify other domains continue → restart Odoo → verify operations resume.

---

## Phase 10: User Story 8 — Ralph Wiggum Loop (Priority: P8)

**Goal**: Autonomous multi-step task completion using Claude Code Stop hook with file-movement completion strategy

**Independent Test**: Create a multi-step task file in Tasks/. Run Claude Code. Verify it executes steps autonomously, pauses for approvals, stops when task moves to Done/ or max iterations reached.

**Dependencies**: Requires US4 (cross-domain), US6 (audit logging), US7 (error recovery)

### Implementation for User Story 8

- [x] T035 [US8] Create `scripts/ralph-wiggum-check.sh` — Stop hook bash script per research.md: read counter from /tmp/ralph-wiggum-counter, increment, check max iterations (read from RALPH_WIGGUM_MAX_ITERATIONS env var, default 10). Check if files exist in `$CLAUDE_PROJECT_DIR/AI_Employee_Vault/Tasks/`. If files remain and under max → exit 1 (continue) with stdout listing remaining tasks. If no files or max reached → exit 0 (stop) and cleanup counter file. Make executable (chmod +x)
- [x] T036 [US8] Create/update `.claude/settings.json` — add Stop hook configuration: `"hooks": { "Stop": [{ "matcher": "", "command": "./scripts/ralph-wiggum-check.sh" }] }`. Preserve any existing settings (permissions, etc.)
- [x] T037 [US8] Add vault `Tasks/` directory creation to `_run_setup()` in `src/main.py`

**Checkpoint**: Ralph Wiggum loop functional. Test: place TASK_*.md in Tasks/ → Claude completes all steps → file moves to Done/ → loop exits.

---

## Phase 11: User Story 9 — Multiple MCP Servers Architecture (Priority: P9)

**Goal**: All 4 MCP servers registered, independently operational, health-monitored

**Independent Test**: Start all MCP servers. Verify each responds to tool calls. Confirm health status for all in .state/health.json.

**Note**: Individual MCP servers created in US1, US2, US3. This phase validates architecture completeness.

### Implementation for User Story 9

- [x] T038 [US9] Validate `.mcp.json` has all 4 servers registered: fte-email, fte-odoo, fte-facebook, fte-instagram. Ensure consistent format. Add env vars if needed for credential passthrough
- [x] T039 [US9] Add MCP server health check integration — in `src/orchestrator/component_health.py`, add `check_mcp_health(server_name)` method that verifies each registered MCP server is reachable. Call on orchestrator startup and periodically

**Checkpoint**: All MCP servers operational and health-monitored.

---

## Phase 12: User Story 10 — Enhanced Dashboard and Agent Skills (Priority: P10)

**Goal**: Dashboard shows all Gold tier metrics; all AI functionality implemented as Agent Skills

**Independent Test**: Open Dashboard.md after running system. Verify Odoo financial data, social media metrics, and system health for all components are displayed.

**Dependencies**: Requires all previous user stories

### Implementation for User Story 10

- [x] T040 [US10] Extend `src/utils/dashboard.py` — add new sections to `update_dashboard()`: Financial Summary (Odoo data: revenue, pending invoices, expenses), Social Media (Facebook: post count, engagement, last post; Instagram: post count, engagement, last post), System Health table (all 5 components with status and last check from `.state/health.json`), Cross-Domain Workflow status (active/completed/failed counts from recent logs). Read data from vault files and health state — do NOT call MCP servers from dashboard (use cached data)
- [x] T041 [US10] Extend `src/main.py` — add Gold tier commands: `odoo` (test Odoo MCP), `facebook` (test Facebook MCP), `instagram` (test Instagram MCP), `briefing` (manually trigger CEO Briefing). Update `_run_setup()` to create Gold directories (Briefings/, Tasks/). Update `_print_help()` with Gold tier commands. Update description to "Gold Tier Autonomous Employee"
- [x] T042 [US10] Verify all 6 Gold tier Agent Skills exist in `.claude/skills/`: `odoo_accountant.md` (T014), `facebook_poster.md` (T018), `instagram_manager.md` (T022), `ceo_briefing.md` (T029), `audit_logger.md` (T030), `error_handler.md` (T034). Check each has: purpose, platform, inputs, steps, approval rules, output format, error handling

**Checkpoint**: Dashboard displays full Gold tier metrics. All 6 Agent Skills verified.

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final integration

- [x] T043 [P] Create `docs/architecture.md` — system design document covering: high-level architecture diagram (text), MCP server structure (4 servers, tools, backends), data flows (trigger → orchestrator → MCP → external → vault), cross-domain integration points, Ralph Wiggum loop flow, approval workflow, audit logging pipeline. Reference all Gold tier source files
- [x] T044 [P] Create `docs/lessons-learned.md` — document challenges, solutions, and recommendations: technology decisions rationale, integration difficulties, security considerations, performance observations, recommendations for future development (Platinum tier)
- [x] T045 Run `specs/003-gold-fte-autonomous/quickstart.md` validation — execute each quickstart step, verify all commands work, fix any discrepancies between quickstart and actual implementation
- [x] T046 Security hardening review — verify: all credentials in .env (not in code, vault, or .mcp.json), .env in .gitignore, audit logs don't contain tokens/passwords, all MCP servers load from env vars, no hardcoded secrets anywhere

---

## Phase 14: OPTIONAL — Twitter and Personal Facebook (Priority: P11-P12)

**Purpose**: Playwright-based automation for platforms without free API access. Only implement if ALL core features (T001-T046) are complete and tested.

- [ ] T047 [US11] (OPTIONAL) Create Twitter/X Playwright automation — `src/watchers/twitter_poster.py` using Playwright with persistent context. Login flow, `post_tweet(text)` method, approval workflow. Test account only
- [ ] T048 [US12] (OPTIONAL) Create personal Facebook profile Playwright automation — `src/watchers/facebook_personal_poster.py` using Playwright with persistent context. Login flow, `post_to_profile(text)` method, approval workflow. Account ban risk accepted

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 Odoo (Phase 3)**: Depends on Phase 2
- **US2 Facebook (Phase 4)**: Depends on Phase 2 + T015 (_meta_client.py)
- **US3 Instagram (Phase 5)**: Depends on Phase 2 + T015 (_meta_client.py shared with US2)
- **US4 Cross-Domain (Phase 6)**: Depends on US1 + US2 + US3
- **US5 CEO Briefing (Phase 7)**: Depends on US4
- **US6 Audit Logging (Phase 8)**: Core in Phase 2; skill + integration after US1-US3
- **US7 Error Recovery (Phase 9)**: Core in Phase 2; integration after US1-US3
- **US8 Ralph Wiggum (Phase 10)**: Depends on US4 + US6 + US7
- **US9 MCP Architecture (Phase 11)**: Validates US1 + US2 + US3
- **US10 Dashboard + Skills (Phase 12)**: Depends on all above
- **Polish (Phase 13)**: Depends on all user stories
- **Optional (Phase 14)**: Only after Phase 13 complete

### User Story Dependencies

```
Phase 2 (Foundation) ─────────────────────┐
    ├── US1 (Odoo) ──────────────────────┤
    ├── US2 (Facebook) ──────────────────┤──→ US4 (Cross-Domain) ──→ US5 (CEO Briefing)
    ├── US3 (Instagram) ─────────────────┤                      ──→ US8 (Ralph Wiggum)
    ├── US6 (Audit - skill) ─────────────┘
    └── US7 (Error - integration) ───────┘
                                           ──→ US9 (MCP Validation)
                                           ──→ US10 (Dashboard + Skills)
                                           ──→ Phase 13 (Polish)
                                           ──→ Phase 14 (Optional)
```

### Within Each User Story

- MCP server before Agent Skill
- Agent Skill before orchestrator integration
- MCP registration (.mcp.json) after server creation
- .env.example updates can be parallel with server creation

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005 are all parallel (different directories)
- **Phase 2**: T007, T008, T009 are all parallel (different files). T006 should complete first (logger used by others)
- **US1, US2, US3**: Can start in parallel after Phase 2 — but US2 and US3 share T015 (_meta_client), so T015 must complete before T016 and T019
- **US6, US7**: Skill creation (T030, T034) can parallel with MCP server work
- **Phase 13**: T043, T044 are parallel (different files)

---

## Parallel Example: Phase 2 Foundation

```bash
# First: complete T006 (logger enhancement — others depend on it)
Task: "Extend src/utils/logger.py with new Gold tier fields"

# Then launch in parallel:
Task: "Create src/utils/audit_retention.py — 90-day retention policy"
Task: "Create src/utils/retry.py — exponential backoff decorator"
Task: "Create src/orchestrator/component_health.py — health registry"
```

## Parallel Example: US1 + US2 + US3 (after Foundation)

```bash
# T015 first (shared by US2 and US3):
Task: "Create src/mcp/_meta_client.py — shared Meta Graph API client"

# Then all three in parallel:
# Developer A: US1
Task: "Create config/docker-compose.yml — Odoo + PostgreSQL"
Task: "Create src/mcp/odoo_server.py — 6 tools"

# Developer B: US2
Task: "Create src/mcp/facebook_server.py — 5 tools"

# Developer C: US3
Task: "Create src/mcp/instagram_server.py — 6 tools"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundation (T006-T009)
3. Complete Phase 3: US1 Odoo (T010-T014)
4. **STOP and VALIDATE**: Test Odoo MCP independently — create invoice, check Odoo web UI
5. Demo if ready

### Incremental Delivery

1. Setup + Foundation → Foundation ready
2. Add US1 (Odoo) → Test → Demo (MVP!)
3. Add US2 (Facebook) + US3 (Instagram) → Test each → Demo
4. Add US4 (Cross-Domain) → Test end-to-end workflow → Demo
5. Add US5 (CEO Briefing) → Test weekly report → Demo
6. Add US6-US10 (Logging, Recovery, Ralph Wiggum, Dashboard) → Full Gold Demo
7. Phase 13 (Documentation) → Production-ready
8. Phase 14 (Optional) → Extra credit

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story independently testable at its checkpoint
- Total core tasks: 46 (T001-T046)
- Optional tasks: 2 (T047-T048)
- Parallel opportunities: 15+ tasks can run in parallel across phases
- Estimated new files: ~15 (MCP servers, utilities, skills, config, scripts)
- Estimated modified files: ~5 (logger.py, dashboard.py, orchestrator.py, approval_handler.py, main.py, .mcp.json)
