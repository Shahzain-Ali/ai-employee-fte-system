# System Architecture: Personal AI Employee — Gold Tier

## High-Level Architecture

```
                    ┌─────────────────────────────────────┐
                    │         Claude Code (CLI)            │
                    │  ┌──────────┐  ┌──────────────────┐ │
                    │  │  Skills  │  │  MCP Servers (4)  │ │
                    │  └──────────┘  └──────────────────┘ │
                    └──────────┬──────────────┬───────────┘
                               │              │
         ┌─────────────────────┤              ├─────────────────────┐
         │                     │              │                     │
    ┌────▼────┐          ┌─────▼─────┐  ┌─────▼─────┐        ┌─────▼─────┐
    │fte-email│          │ fte-odoo  │  │fte-facebook│        │fte-insta  │
    │ (Node)  │          │ (Python)  │  │ (Python)   │        │ (Python)  │
    └────┬────┘          └─────┬─────┘  └─────┬──────┘        └─────┬─────┘
         │                     │              │                     │
    Gmail API            Odoo Docker     Meta Graph API       Meta Graph API
                       (JSON-RPC)         (Facebook)          (Instagram)
```

## Data Flow

```
Trigger (Email/WhatsApp/File) → Watcher → Needs_Action/ → Orchestrator
  → Resolve Skill → Claude Code → MCP Tool Call → External API
  → Result → Audit Log → Done/ → Dashboard Update
```

## MCP Server Architecture

| Server | Tools | Backend | Transport |
|--------|-------|---------|-----------|
| fte-email | send_email, draft_email | Gmail API | stdio (Node.js) |
| fte-odoo | create_invoice, get_invoices, mark_payment, get_summary, get_expenses, create_expense | Odoo JSON-RPC | stdio (Python) |
| fte-facebook | create_page_post, get_posts, get_comments, reply_comment, get_insights | Meta Graph API v21.0 | stdio (Python) |
| fte-instagram | create_ig_post, create_ig_reel, get_media, get_comments, reply_comment, get_insights | Meta Graph API v21.0 | stdio (Python) |

## Cross-Domain Integration

WorkflowEngine generates unique workflow_id (UUID) linking all actions:

```
Email trigger → WorkflowEngine.start_workflow()
  Step 1: Create Odoo invoice (ODOO_ action file)
  Step 2: Send email confirmation (EMAIL_ action file)
  Step 3: Post on Facebook (FB_ action file)
  All logged with same workflow_id
```

## Ralph Wiggum Loop

```
Claude Code starts → processes tasks
  → Stop hook fires (ralph-wiggum-check.sh)
  → Checks Tasks/ directory for TASK_*.md files
  → Files remain? exit 1 (continue) : exit 0 (stop)
  → Max iterations? exit 0 (stop)
```

## Approval Workflow

ALL external actions require human approval:
1. AI creates `APPROVAL_*.md` in `Pending_Approval/`
2. Owner reviews content
3. Owner moves file to `Approved/` or `Rejected/`
4. ApprovalWatcher detects move
5. ApprovalHandler executes approved action

## Audit Logging Pipeline

```
Action → LogEntry (dataclass) → AuditLogger.log()
  → Logs/YYYY-MM-DD.json (JSON array)
  → 90-day retention (daily cron at 03:00)
```

## Source Files

### MCP Servers
- `src/mcp/odoo_server.py` — Odoo JSON-RPC (6 tools)
- `src/mcp/facebook_server.py` — Facebook Graph API (5 tools)
- `src/mcp/instagram_server.py` — Instagram Graph API (6 tools)
- `src/mcp/_meta_client.py` — Shared Meta API client

### Orchestration
- `src/orchestrator/orchestrator.py` — File-based action routing
- `src/orchestrator/approval_handler.py` — HITL approval execution
- `src/orchestrator/workflow_engine.py` — Cross-domain workflows
- `src/orchestrator/component_health.py` — Health tracking

### Utilities
- `src/utils/logger.py` — Structured audit logging
- `src/utils/retry.py` — Exponential backoff
- `src/utils/audit_retention.py` — 90-day log cleanup
- `src/utils/ceo_briefing.py` — Weekly briefing generator
- `src/utils/dashboard.py` — Dashboard updater

### Agent Skills (12 total)
- Bronze: process_document, update_dashboard, create_approval_request
- Silver: email_responder, whatsapp_handler, plan_creator
- Gold: odoo_accountant, facebook_poster, instagram_manager, ceo_briefing, audit_logger, error_handler
