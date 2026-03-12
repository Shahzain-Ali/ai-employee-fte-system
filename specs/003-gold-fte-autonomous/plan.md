# Implementation Plan: Gold Tier — Autonomous Employee

**Branch**: `main` | **Date**: 2026-02-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/003-gold-fte-autonomous/spec.md`

---

## Summary

Gold tier transforms the Silver tier Functional Assistant into a fully Autonomous Employee
by adding: Odoo accounting integration (Docker + JSON-RPC via custom MCP server), Facebook
Business Page integration (Meta Graph API via custom MCP server), Instagram Business Account
integration (Meta Graph API via custom MCP server with content publishing), full cross-domain
integration (Personal + Business triggers cascade across domains), weekly CEO Briefing
generation, comprehensive structured audit logging, error recovery with graceful degradation,
Ralph Wiggum autonomous loop (Stop hook with file-movement completion), and all AI
functionality as Agent Skills. Optional: Twitter/X and personal Facebook profile via Playwright.

---

## Technical Context

**Language/Version**: Python 3.14.3 (WSL) — managed via `uv`
**Primary Dependencies**: mcp[cli]>=1.26.0 (MCP servers), requests>=2.31.0 (HTTP/JSON-RPC), APScheduler (scheduling), watchdog (filesystem), playwright (optional: Twitter/FB personal)
**Storage**: Obsidian vault (markdown + JSON), PostgreSQL 16 (Odoo Docker), SQLite (APScheduler jobs)
**Testing**: pytest + pytest-asyncio
**Target Platform**: WSL2 (Linux 6.6.87.2-microsoft-standard-WSL2)
**Project Type**: Single project — extends existing `src/` structure
**Performance Goals**: MCP tool response <30s, CEO Briefing generation <5min, audit log write <100ms
**Constraints**: Local-first (no cloud), all secrets in .env, HITL approval for all external actions
**Scale/Scope**: Single user (owner), 4 MCP servers, 5 integrated domains, ~12 new source files

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I | Local-First Architecture | ✅ PASS | Odoo runs locally via Docker. All data in vault. Meta API tokens in .env. No cloud services store data. |
| II | Human-in-the-Loop (HITL) Safety | ✅ PASS | All Facebook/Instagram posts require approval. All Odoo payment actions require approval. Ralph Wiggum loop pauses for approval-required steps. FR-026: payments never auto-retried. |
| III | Agent Skills First | ✅ PASS | 6 new Agent Skills defined: odoo_accountant, facebook_poster, instagram_manager, ceo_briefing, audit_logger, error_handler. All Gold AI logic in skills. |
| IV | Documentation-First Development | ✅ PASS | Full spec → plan → tasks workflow followed. Research completed for all technologies. |
| V | Security by Design | ✅ PASS | All credentials in .env. Custom MCP servers only (no third-party). Audit logs exclude sensitive data (FR-022). .secrets/ in .gitignore. |
| VI | Tiered Complexity Growth | ✅ PASS | Silver tier is complete and functional. Gold builds incrementally on Silver foundation. No Platinum features included. |

**Gate Result**: ✅ ALL PASS — proceed to implementation.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-gold-fte-autonomous/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 research (complete)
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 quickstart guide
├── contracts/           # Phase 1 MCP tool contracts
│   ├── fte-odoo.md
│   ├── fte-facebook.md
│   └── fte-instagram.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Phase 2 task list (created by /sp.tasks)
```

### Source Code (repository root)

```text
src/
├── main.py                          # Entry point (extend with gold commands)
├── mcp/
│   ├── index.js                     # Existing Node.js email MCP (to be retired)
│   ├── email_server.py              # Existing Python email MCP
│   ├── odoo_server.py               # NEW: Odoo MCP server
│   ├── facebook_server.py           # NEW: Facebook MCP server
│   ├── instagram_server.py          # NEW: Instagram MCP server
│   └── _meta_client.py              # NEW: Shared Meta Graph API client
├── orchestrator/
│   ├── orchestrator.py              # Extend with cross-domain workflows
│   ├── approval_handler.py          # Extend with FB/IG/Odoo approval types
│   ├── approval_watcher.py          # Existing (no changes expected)
│   ├── workflow_engine.py           # NEW: Cross-domain workflow executor
│   └── component_health.py          # NEW: Component health registry
├── watchers/
│   ├── filesystem_watcher.py        # Existing (no changes)
│   ├── gmail_watcher.py             # Existing (no changes)
│   ├── gmail_auth.py                # Existing (no changes)
│   ├── whatsapp_watcher.py          # Existing (no changes)
│   └── base_watcher.py              # Existing (no changes)
├── utils/
│   ├── logger.py                    # Extend: add workflow_id, duration_ms, mcp_server fields
│   ├── dashboard.py                 # Extend: add Odoo, social media, health sections
│   ├── email_sender.py              # Existing (no changes)
│   ├── whatsapp_sender.py           # Existing (no changes)
│   ├── plan_manager.py              # Existing (no changes)
│   ├── retry.py                     # NEW: Exponential backoff retry utility
│   ├── audit_retention.py           # NEW: 90-day log retention policy
│   └── ceo_briefing.py              # NEW: CEO Briefing data collector + generator
├── __init__.py
└── scheduler/
    └── jobs.py                      # NEW: Gold tier scheduled jobs (CEO briefing)

config/
├── schedules.json                   # Extend with CEO briefing schedule
└── docker-compose.yml               # NEW: Odoo + PostgreSQL

scripts/
└── ralph-wiggum-check.sh            # NEW: Stop hook for autonomous loop

.claude/skills/
├── process_document.md              # Existing (Bronze)
├── update_dashboard.md              # Existing (Bronze)
├── create_approval_request.md       # Existing (Bronze)
├── email_responder.md               # Existing (Silver)
├── whatsapp_handler.md              # Existing (Silver)
├── plan_creator.md                  # Existing (Silver)
├── odoo_accountant.md               # NEW: Odoo invoice/payment/expense management
├── facebook_poster.md               # NEW: Facebook Page posting and engagement
├── instagram_manager.md             # NEW: Instagram publishing and engagement
├── ceo_briefing.md                  # NEW: Weekly CEO Briefing generation
├── audit_logger.md                  # NEW: Structured audit logging
└── error_handler.md                 # NEW: Error recovery and degradation

.claude/settings.json                # NEW/UPDATE: Add Ralph Wiggum Stop hook
.mcp.json                           # UPDATE: Add 3 new MCP servers
```

**Structure Decision**: Extends existing `src/` single-project structure. New files follow established patterns (MCP servers in `src/mcp/`, utilities in `src/utils/`, skills in `.claude/skills/`). No new top-level directories needed except `scripts/` for the Ralph Wiggum hook.

---

## Implementation Phases

### Phase A: Infrastructure & Foundation (P1, P6, P7, P9)

**Goal**: Set up Odoo Docker, audit logging, error recovery, and MCP server architecture.

**Rationale**: These are foundational — every other feature depends on audit logging (P6),
error recovery (P7), and the MCP server pattern (P9). Odoo (P1) is the business domain
foundation.

1. **Audit Logging Enhancement** (P6)
   - Extend `src/utils/logger.py` LogEntry with: `workflow_id`, `duration_ms`, `mcp_server`, `retry_count`, `error_message`
   - Add `audit_retention.py` for 90-day cleanup
   - All subsequent features use this enhanced logging
   - Files: `src/utils/logger.py` (modify), `src/utils/audit_retention.py` (new)

2. **Error Recovery Utility** (P7)
   - Create `src/utils/retry.py` with `retry_with_backoff()` decorator
   - Create `src/orchestrator/component_health.py` for health tracking
   - All MCP servers and workflows use this utility
   - Files: `src/utils/retry.py` (new), `src/orchestrator/component_health.py` (new)

3. **Odoo Docker Setup** (P1 — infrastructure)
   - Create `config/docker-compose.yml` (Odoo 19 + PostgreSQL 16)
   - Add `.env` entries: `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`
   - Test: `docker-compose up -d` and access http://localhost:8069
   - Files: `config/docker-compose.yml` (new), `.env` (modify)

4. **Odoo MCP Server** (P1 — integration)
   - Create `src/mcp/odoo_server.py` with tools: `create_invoice`, `get_invoices`, `mark_payment_received`, `get_weekly_summary`, `get_expenses`, `create_expense`
   - Uses JSON-RPC via `requests` library
   - Register in `.mcp.json` as `fte-odoo`
   - Files: `src/mcp/odoo_server.py` (new), `.mcp.json` (modify)

5. **Odoo Agent Skill** (P1 — skill)
   - Create `.claude/skills/odoo_accountant.md`
   - Files: `.claude/skills/odoo_accountant.md` (new)

### Phase B: Social Media Integration (P2, P3)

**Goal**: Facebook and Instagram MCP servers with posting and engagement features.

**Prerequisite**: Phase A complete (audit logging + error recovery available)

6. **Shared Meta Graph API Client**
   - Create `src/mcp/_meta_client.py` — shared HTTP client for Meta Graph API
   - Handles authentication, token management, rate limit detection
   - Used by both Facebook and Instagram servers
   - Files: `src/mcp/_meta_client.py` (new)

7. **Facebook MCP Server** (P2)
   - Create `src/mcp/facebook_server.py` with tools: `create_page_post`, `get_page_posts`, `get_post_comments`, `reply_to_comment`, `get_page_insights`
   - Register in `.mcp.json` as `fte-facebook`
   - Files: `src/mcp/facebook_server.py` (new), `.mcp.json` (modify)

8. **Facebook Agent Skill** (P2 — skill)
   - Create `.claude/skills/facebook_poster.md`
   - Files: `.claude/skills/facebook_poster.md` (new)

9. **Instagram MCP Server** (P3)
   - Create `src/mcp/instagram_server.py` with tools: `create_ig_post`, `create_ig_reel`, `get_ig_media`, `get_ig_comments`, `reply_ig_comment`, `get_ig_insights`
   - Uses 2-step container publishing flow
   - Register in `.mcp.json` as `fte-instagram`
   - Files: `src/mcp/instagram_server.py` (new), `.mcp.json` (modify)

10. **Instagram Agent Skill** (P3 — skill)
    - Create `.claude/skills/instagram_manager.md`
    - Files: `.claude/skills/instagram_manager.md` (new)

### Phase C: Cross-Domain & Autonomous Loop (P4, P8)

**Goal**: Connect all domains and enable autonomous multi-step execution.

**Prerequisite**: Phase A + B complete (all MCP servers operational)

11. **Cross-Domain Workflow Engine** (P4)
    - Create `src/orchestrator/workflow_engine.py` — executes multi-domain workflows
    - Shared `workflow_id` links actions across domains in audit logs
    - Handles partial failures: completed steps preserved, failed step logged
    - Files: `src/orchestrator/workflow_engine.py` (new)

12. **Orchestrator Extension** (P4)
    - Extend `src/orchestrator/orchestrator.py` to route cross-domain triggers
    - Extend `src/orchestrator/approval_handler.py` with Facebook/Instagram/Odoo approval types
    - Add new action file prefixes: `ODOO_`, `FB_`, `IG_`
    - Files: `src/orchestrator/orchestrator.py` (modify), `src/orchestrator/approval_handler.py` (modify)

13. **Ralph Wiggum Stop Hook** (P8)
    - Create `scripts/ralph-wiggum-check.sh` — checks if task file moved to /Done
    - Update `.claude/settings.json` with Stop hook configuration
    - Create vault `Tasks/` directory for Ralph Wiggum task files
    - Files: `scripts/ralph-wiggum-check.sh` (new), `.claude/settings.json` (new/modify)

14. **Error Handler Agent Skill** (P7 — skill)
    - Create `.claude/skills/error_handler.md`
    - Files: `.claude/skills/error_handler.md` (new)

### Phase D: Intelligence & Dashboard (P5, P10)

**Goal**: CEO Briefing, enhanced dashboard, and remaining skills.

**Prerequisite**: Phase C complete (all domains connected)

15. **CEO Briefing Generator** (P5)
    - Create `src/utils/ceo_briefing.py` — collects data from all domains
    - Add APScheduler job for Sunday night trigger
    - Create vault `Briefings/` directory
    - Files: `src/utils/ceo_briefing.py` (new), `src/scheduler/jobs.py` (new), `config/schedules.json` (modify)

16. **CEO Briefing Agent Skill** (P5 — skill)
    - Create `.claude/skills/ceo_briefing.md`
    - Files: `.claude/skills/ceo_briefing.md` (new)

17. **Audit Logger Agent Skill** (P6 — skill)
    - Create `.claude/skills/audit_logger.md`
    - Files: `.claude/skills/audit_logger.md` (new)

18. **Enhanced Dashboard** (P10)
    - Extend `src/utils/dashboard.py` with Odoo financial data, social media metrics, component health, cross-domain workflow status
    - Files: `src/utils/dashboard.py` (modify)

19. **Entry Point Extension** (P10)
    - Extend `src/main.py` with Gold tier commands: `odoo`, `facebook`, `instagram`, `briefing`
    - Add vault setup for Gold directories: `Briefings/`, `Tasks/`
    - Files: `src/main.py` (modify)

### Phase E: Documentation (P10 — FR-036, FR-037)

**Goal**: Architecture documentation and lessons learned.

20. **Architecture Documentation**
    - Create `docs/architecture.md` — system design, MCP server structure, data flows, integration points
    - Files: `docs/architecture.md` (new)

21. **Lessons Learned Documentation**
    - Create `docs/lessons-learned.md` — challenges, solutions, recommendations
    - Files: `docs/lessons-learned.md` (new)

### Phase F: Optional Features (P11, P12)

**Goal**: Twitter and personal Facebook profile via Playwright (only if time permits).

**Prerequisite**: All core features (Phase A-E) complete and tested.

22. **Twitter/X Playwright Automation** (P11 — OPTIONAL)
    - Create `src/mcp/twitter_server.py` or `src/watchers/twitter_poster.py`
    - Files: TBD if implemented

23. **Personal Facebook Profile Playwright** (P12 — OPTIONAL)
    - Create `src/watchers/facebook_personal_poster.py`
    - Files: TBD if implemented

---

## Dependency Graph

```
Phase A: Infrastructure
  ├── [1] Audit Logging Enhancement ─────────────┐
  ├── [2] Error Recovery Utility ────────────────┤
  ├── [3] Odoo Docker Setup ─────→ [4] Odoo MCP → [5] Odoo Skill
  └── MCP Server Pattern (established) ──────────┘
                                                   │
Phase B: Social Media                              │
  ├── [6] Meta Client ──→ [7] Facebook MCP → [8] FB Skill
  └── [6] Meta Client ──→ [9] Instagram MCP → [10] IG Skill
                                                   │
Phase C: Cross-Domain                              │
  ├── [11] Workflow Engine ←── needs [4]+[7]+[9]   │
  ├── [12] Orchestrator Extension ←── needs [11]   │
  ├── [13] Ralph Wiggum Stop Hook                  │
  └── [14] Error Handler Skill                     │
                                                   │
Phase D: Intelligence                              │
  ├── [15] CEO Briefing Generator ←── needs [11]   │
  ├── [16] CEO Briefing Skill                      │
  ├── [17] Audit Logger Skill                      │
  ├── [18] Enhanced Dashboard ←── needs all above  │
  └── [19] Entry Point Extension                   │
                                                   │
Phase E: Documentation                             │
  ├── [20] Architecture Docs                       │
  └── [21] Lessons Learned                         │
                                                   │
Phase F: Optional (if time permits)                │
  ├── [22] Twitter Playwright (OPTIONAL)           │
  └── [23] Personal FB Playwright (OPTIONAL)       │
```

---

## Key Architecture Decisions

### 1. Python for ALL MCP Servers

**Decision**: Use Python MCP SDK for all servers (including migrating email from Node.js).

**Rationale**: Single language ecosystem, direct library imports, existing `email_server.py` pattern. The Node.js `index.js` can be retired once Python email server is verified.

### 2. Shared Meta Graph API Client

**Decision**: Extract shared HTTP client for Meta API into `_meta_client.py`.

**Rationale**: Both Facebook and Instagram use Meta Graph API. Shared client handles authentication, token refresh, rate limit detection, and error formatting — avoiding code duplication.

### 3. Workflow Engine (Not Ad-Hoc Cross-Domain)

**Decision**: Create dedicated `workflow_engine.py` for cross-domain orchestration.

**Rationale**: Cross-domain workflows need: shared workflow_id, partial failure handling, step tracking, and audit trail. Ad-hoc calls between MCP servers would lack traceability.

### 4. Ralph Wiggum as Shell Script (Not Python)

**Decision**: Implement Stop hook as a bash script.

**Rationale**: Claude Code hooks execute shell commands. A bash script is the simplest, most reliable approach — just check file existence and exit 0/1.

---

## Complexity Tracking

> No Constitution violations detected. All features follow established patterns.

| Concern | Justification |
|---------|---------------|
| 4 MCP servers simultaneously | Each is independent, single-responsibility. Claude Code handles multi-server connections natively. |
| Docker dependency (Odoo) | Required by hackathon specification. Isolated via docker-compose, no system-level installation. |
| Ralph Wiggum Stop hook | Minimal shell script. Adds autonomous capability without complex architecture. |

---

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Meta Graph API App Review required for production permissions | Cannot post to FB/IG without review | Use Development Mode (limited to test users) for demo; document App Review process |
| Odoo Docker resource usage on WSL | May slow system with limited RAM | Monitor memory; Odoo can be stopped when not needed |
| Instagram 25-post daily limit | Unlikely to hit in normal use | Track count in audit logs; warn at 20 posts |

---

## Post-Design Constitution Re-Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Local-First | ✅ PASS | Odoo Docker is local. Meta API tokens stored locally. No cloud data storage. |
| II | HITL Safety | ✅ PASS | All posts/payments require approval. Ralph Wiggum pauses for approval steps. |
| III | Agent Skills First | ✅ PASS | 6 new skills cover all Gold AI functionality. |
| IV | Documentation-First | ✅ PASS | Spec → Research → Plan → Tasks workflow. Architecture docs in Phase E. |
| V | Security by Design | ✅ PASS | Custom MCP servers. Secrets in .env. Audit logs scrub sensitive data. |
| VI | Tiered Complexity | ✅ PASS | Builds on complete Silver tier. No Platinum features. |
