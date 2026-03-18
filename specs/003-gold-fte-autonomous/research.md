# Research: Gold Tier Technology Decisions

**Feature**: 003-gold-fte-autonomous
**Date**: 2026-02-24
**Status**: Complete

---

## 1. Odoo Community Edition Integration

### Decision: Docker (docker-compose) + JSON-RPC API via Python `requests`

**Rationale**:
- Odoo Community Edition is free and self-hosted (Constitution Principle I: Local-First)
- Docker provides isolated, reproducible deployment
- JSON-RPC is the recommended external API for Odoo 17+
- Python `requests` library makes HTTP-based JSON-RPC calls simple

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| JSON-RPC via `requests` | Simple HTTP calls, stateless | No persistent session | Selected |
| XML-RPC via `xmlrpc.client` | Built-in Python, well-documented | Older protocol, less flexible | JSON-RPC is modern standard |
| OdooRPC library | Convenient wrapper | Extra dependency, may lag Odoo versions | Direct JSON-RPC is more reliable |
| Odoo REST API (Community module) | RESTful | Requires installing community module | Adds complexity |

**Technical Details**:

- **Docker Image**: `odoo:19` (stable, released October 2025) — matches hackathon requirement (Odoo 19+)
- **PostgreSQL**: Version 15 or 16 recommended (minimum 12 for Odoo 17+)
- **JSON-RPC Endpoint**: `POST http://localhost:8069/jsonrpc`
- **Authentication**: Database name + username + password on every call (stateless)
- **Key Models**: `account.move` (invoices), `account.payment` (payments), `hr.expense` (expenses)

**JSON-RPC Call Pattern**:
```python
import requests

def odoo_jsonrpc(url, method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(f"{url}/jsonrpc", json=payload)
    result = response.json()
    if "error" in result:
        raise Exception(result["error"]["data"]["message"])
    return result["result"]

# Authenticate
uid = odoo_jsonrpc(url, "call", {
    "service": "common",
    "method": "authenticate",
    "args": [db, username, password, {}]
})

# Create invoice
invoice_id = odoo_jsonrpc(url, "call", {
    "service": "object",
    "method": "execute_kw",
    "args": [db, uid, password, "account.move", "create", [{
        "move_type": "out_invoice",
        "partner_id": partner_id,
        "invoice_line_ids": [(0, 0, {
            "name": "Service",
            "quantity": 1,
            "price_unit": 500.00
        })]
    }]]
})
```

**Docker Compose**:
```yaml
services:
  odoo:
    image: odoo:19
    ports:
      - "8069:8069"
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo
    volumes:
      - odoo-data:/var/lib/odoo
    depends_on:
      - db
  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_USER=odoo
    volumes:
      - pg-data:/var/lib/postgresql/data

volumes:
  odoo-data:
  pg-data:
```

**Required Packages**:
```
requests>=2.31.0  # Already likely installed; for JSON-RPC calls
```

---

## 2. Meta Graph API (Facebook + Instagram)

### Decision: Meta Graph API v21.0+ via custom Python MCP servers

**Rationale**:
- Official, stable API for Facebook Pages and Instagram Business/Creator accounts (Instagram Platform API supports Creator since July 2024)
- Non-expiring Page access tokens for server-to-server integration
- Single Meta Developer Account controls both platforms
- Security first — custom MCP servers, no third-party (Constitution Principle V)

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Meta Graph API (custom MCP) | Official, stable, free | Setup complexity | Selected |
| Community MCP (meta-pages-mcp) | Pre-built, 35 tools | Third-party, security risk | Constitution Principle V |
| Playwright automation | Works on personal profiles | Account ban risk, fragile | Optional only (P11/P12) |

**Technical Details**:

**Facebook Pages API**:
- **Create post**: `POST https://graph.facebook.com/v21.0/{page-id}/feed` (params: `message`, `access_token`)
- **Get posts**: `GET https://graph.facebook.com/v21.0/{page-id}/feed` (returns posts with engagement)
- **Get comments**: `GET https://graph.facebook.com/v21.0/{post-id}/comments`
- **Reply to comment**: `POST https://graph.facebook.com/v21.0/{comment-id}/comments` (params: `message`)
- **Page insights**: `GET https://graph.facebook.com/v21.0/{page-id}/insights` (params: `metric`, `period`)

**Required Permissions**: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`

**Instagram Content Publishing API** (2-step container flow):
- **Step 1 — Create container**: `POST https://graph.facebook.com/v21.0/{ig-user-id}/media` (params: `image_url`/`video_url`, `caption`, `media_type`)
- **Step 2 — Publish**: `POST https://graph.facebook.com/v21.0/{ig-user-id}/media_publish` (params: `creation_id`)
- **Get media**: `GET https://graph.facebook.com/v21.0/{ig-user-id}/media`
- **Get comments**: `GET https://graph.facebook.com/v21.0/{media-id}/comments`
- **Reply to comment**: `POST https://graph.facebook.com/v21.0/{comment-id}/replies`
- **Insights**: `GET https://graph.facebook.com/v21.0/{ig-user-id}/insights`

**Required Permissions**: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`

**Non-Expiring Page Access Token Flow**:
1. Get short-lived user token from Meta Developer Portal
2. Exchange for long-lived user token: `GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived}`
3. Get Page token using long-lived user token: `GET /me/accounts?access_token={long-lived-user-token}`
4. The Page token in response **never expires**

**Rate Limits**:
- Facebook Pages: ~4800 calls per Page per 24h rolling window
- Instagram Publishing: **25 posts per account per 24h** (hard limit)
- Instagram API calls: 200 calls per user per hour

**Required Packages**:
```
requests>=2.31.0  # For Graph API HTTP calls
```

---

## 3. MCP Server Architecture

### Decision: Python MCP SDK (`mcp` package) for all new servers

**Rationale**:
- Python `mcp` package already a project dependency (`mcp[cli]>=1.26.0`)
- Working Python MCP server exists at `src/mcp/email_server.py`
- All business logic is Python — avoid two language ecosystems
- Direct import of Python libraries (requests, etc.) without subprocess bridges

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Python MCP SDK | Consistent, direct imports | Async model | Selected |
| Node.js MCP SDK | Existing email server uses it | Two ecosystems | Python preferred |
| REST API wrapper | Language agnostic | Extra network layer | MCP is native |

**Technical Details**:

**Python MCP Server Pattern** (from existing `email_server.py`):
```python
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

server = Server("fte-odoo")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="create_invoice", description="...", inputSchema={...})]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "create_invoice":
        result = create_odoo_invoice(arguments)
        return [TextContent(type="text", text=f"Invoice created: {result}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())
```

**Multiple Servers in .mcp.json**:
```json
{
  "mcpServers": {
    "fte-email": {
      "type": "stdio",
      "command": "python",
      "args": ["src/mcp/email_server.py"],
      "env": {}
    },
    "fte-odoo": {
      "type": "stdio",
      "command": "python",
      "args": ["src/mcp/odoo_server.py"],
      "env": {}
    },
    "fte-facebook": {
      "type": "stdio",
      "command": "python",
      "args": ["src/mcp/facebook_server.py"],
      "env": {}
    },
    "fte-instagram": {
      "type": "stdio",
      "command": "python",
      "args": ["src/mcp/instagram_server.py"],
      "env": {}
    }
  }
}
```

Tool names are auto-namespaced by Claude Code: `mcp__fte-odoo__create_invoice`

**Best Practices**:
- Log to stderr only (stdout is MCP protocol)
- Return errors as TextContent, don't throw (let Claude reason about failures)
- Throw ValueError only for unknown tool names
- Lazy initialization for heavy dependencies
- Load secrets from `.env` via python-dotenv, never from `.mcp.json`

---

## 4. Ralph Wiggum Loop (Stop Hook Pattern)

### Decision: Claude Code Stop hook with file-movement check

**Rationale**:
- Official Claude Code hooks mechanism in `.claude/settings.json`
- Stop hook fires when Claude thinks it's done — non-zero exit forces continuation
- File-movement is reliable and observable (file exists = not done)
- Maximum iteration limit prevents infinite loops

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Stop hook + file-movement | Official mechanism, reliable | Requires hook script | Selected |
| Manual loop in orchestrator | Full control | Not leveraging Claude's autonomy | Less autonomous |
| Counter-based completion | Simple | No semantic completion check | Less intelligent |

**Technical Details**:

**Hook Configuration** (`.claude/settings.json`):
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "command": "./scripts/ralph-wiggum-check.sh"
      }
    ]
  }
}
```

**Stop Hook Script** (`scripts/ralph-wiggum-check.sh`):
```bash
#!/bin/bash
VAULT_DIR="${CLAUDE_PROJECT_DIR}/AI_Employee_Vault"
TASK_DIR="${VAULT_DIR}/Tasks"
MAX_ITERATIONS=10
COUNTER_FILE="/tmp/ralph-wiggum-counter"

# Initialize or read counter
if [ ! -f "$COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi
COUNT=$(cat "$COUNTER_FILE")
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# Check max iterations
if [ "$COUNT" -ge "$MAX_ITERATIONS" ]; then
    echo "Max iterations ($MAX_ITERATIONS) reached. Stopping."
    rm -f "$COUNTER_FILE"
    exit 0  # Allow stop
fi

# Check if task files remain
if [ "$(ls -A "$TASK_DIR" 2>/dev/null)" ]; then
    echo "Tasks remaining in $TASK_DIR: $(ls "$TASK_DIR")"
    echo "Continue processing. Iteration $COUNT/$MAX_ITERATIONS"
    exit 1  # Force continue
fi

# All done
rm -f "$COUNTER_FILE"
exit 0  # Allow stop
```

**Hook Behavior**:
- Exit 0 → Claude stops (task complete or max iterations)
- Exit 1 → Claude continues (stdout fed back as context)
- `CLAUDE_PROJECT_DIR` env var provides project root

---

## 5. Comprehensive Audit Logging

### Decision: Extend existing `AuditLogger` with structured JSON + workflow tracking

**Rationale**:
- `src/utils/logger.py` already has `AuditLogger` and `LogEntry` classes
- Extend with new fields: `workflow_id`, `duration_ms`, `mcp_server`, `retry_count`
- Keep same file-based storage: `vault/Logs/YYYY-MM-DD.json`
- Add 90-day retention policy

**Technical Details**:

**Extended Log Entry Fields**:
```json
{
  "timestamp": "2026-02-24T10:30:00Z",
  "action_type": "invoice_created",
  "actor": "fte-odoo",
  "target": "account.move:42",
  "parameters": {"partner_id": 7, "amount": 500},
  "approval_status": "approved",
  "result": "success",
  "duration_ms": 1250,
  "mcp_server": "fte-odoo",
  "workflow_id": "wf-abc123",
  "error_message": null,
  "retry_count": 0
}
```

---

## 6. Error Recovery and Graceful Degradation

### Decision: Exponential backoff retry + component health registry

**Rationale**:
- Transient errors (network, rate limit) should be retried automatically
- Permanent errors should alert the owner
- System must continue when individual components fail
- Constitution Principle II: payments never auto-retried

**Technical Details**:

**Retry Pattern**:
```python
import time

def retry_with_backoff(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
            time.sleep(delay)
```

**Component Health Registry**: Track status of each domain (Odoo, Facebook, Instagram, Gmail, WhatsApp) with `healthy`, `degraded`, `down` states. Dashboard shows current health.

---

## 7. CEO Briefing Generation

### Decision: APScheduler Sunday night trigger + multi-domain data collection

**Rationale**:
- APScheduler already a project dependency (Silver tier)
- Scheduled task collects data from all domain MCP servers
- Claude generates the briefing markdown using a dedicated Agent Skill
- Graceful handling of missing data sources

**Technical Details**:

**Schedule Configuration**:
```python
scheduler.add_job(
    generate_ceo_briefing,
    CronTrigger(day_of_week='sun', hour=22, minute=0),
    id='ceo_briefing_weekly',
    name='Weekly CEO Briefing'
)
```

**Data Sources**:
1. Odoo MCP → `get_weekly_summary` (revenue, expenses, invoices)
2. Facebook MCP → `get_page_insights` (posts, reach, engagement)
3. Instagram MCP → `get_ig_insights` (media, engagement)
4. Vault files → count Gmail/WhatsApp actions processed this week

**Output**: `AI_Employee_Vault/Briefings/CEO_Briefing_YYYY-MM-DD.md`

---

## Research Complete

All technology decisions finalized. No NEEDS CLARIFICATION items remain.

**Summary of New Dependencies (Gold Tier)**:
```toml
[project.dependencies]
# Existing (Bronze + Silver)
# ... all existing deps ...

# Gold (new)
requests = ">=2.31.0"       # Odoo JSON-RPC + Meta Graph API HTTP calls
```

Note: `requests` is the only new Python package needed. Odoo runs in Docker (no Python dependency). Meta Graph API uses HTTP calls via `requests`. MCP SDK (`mcp`) is already installed.

Proceed with plan.md, data-model.md, contracts/, and quickstart.md.
