# Gold Tier Implementation — Complete Flow Guide

## Overview

This document details the implementation of the Gold Tier autonomous AI employee, specifically the cross-domain flow from email to Odoo invoice with auto-approval and auto-stop containers.

---

## The Complete Flow

```
Real Email (Gmail)
    ↓
Gmail Watcher detects unread email
    ↓
Creates EMAIL_*.md in Needs_Action/
    ↓
Orchestrator polls (60s interval)
    ↓
Claude subprocess starts (claude --print)
    ↓
Email Responder Skill analyzes email
    ↓
Detects "invoice request" keywords
    ↓
[Cross-Domain] Calls create_invoice MCP tool
    ↓
Odoo MCP Server → _ensure_odoo_running()
    ↓
Docker containers START (if not running)
    ↓
Odoo JSON-RPC → Invoice created (ID, Partner, Amount)
    ↓
Calls send_email MCP tool → Reply sent to client
    ↓
Claude subprocess completes → Client disconnects
    ↓
MCP Server idle for 30 seconds
    ↓
MCP Server exits → atexit.register() fires
    ↓
_stop_odoo_containers() → Docker containers STOP
    ↓
Done/ — Summary file created
```

---

## Problems Faced & Solutions

### Problem 1: MCP Servers Not Working in Subprocess

**Issue:** When orchestrator ran Claude subprocess from vault directory (AI_Employee_Vault/), MCP servers (.mcp.json) were not loaded because .mcp.json was in project root.

**Error:** Claude subprocess couldn't access MCP tools (create_invoice, send_email, etc.)

**Solution:**
```python
# orchestrator.py — Changed cwd from vault_path to project_root
project_root = Path(__file__).resolve().parent.parent.parent

result = subprocess.run(
    cmd,
    cwd=str(project_root),  # Was: cwd=str(self.vault_path)
    ...
)
```

---

### Problem 2: Gmail Watcher Not Starting

**Issue:** Gmail watcher kept showing "SKIPPED (no credentials)" even though credentials existed in .secrets/.

**Root Cause:** main.py checked for `GMAIL_CREDENTIALS_PATH` in .env, but it wasn't set.

**Solution:** Added to .env:
```env
GMAIL_CREDENTIALS_PATH=.secrets/gmail_credentials.json
GMAIL_TOKEN_PATH=.secrets/gmail_token.json
```

---

### Problem 3: Gmail Query Too Restrictive

**Issue:** `is:unread is:important` query missed many emails because Gmail's "Important" label is algorithmic.

**Solution:** Changed to simpler query:
```python
# gmail_watcher.py
self._query = os.getenv("GMAIL_QUERY", "is:unread")  # Was: "is:unread is:important"
```

---

### Problem 4: Odoo Containers Not Stopping Automatically

**Issue:** After Claude subprocess completed, Docker containers kept running, consuming resources.

**Root Cause:**
- `atexit.register(_stop_odoo_containers)` only fires on clean process exit
- When Claude subprocess was killed by timeout, atexit didn't fire
- MCP server (stdio mode) stayed alive waiting for more requests

**Solution:** Added idle timeout to MCP server:
```python
# odoo_server.py
IDLE_TIMEOUT = int(os.getenv("MCP_IDLE_TIMEOUT", "30"))

def _update_activity():
    """Update last request timestamp."""
    global _last_request_time
    _last_request_time = time.time()

def _check_idle_and_exit():
    """Background thread: exit if idle for IDLE_TIMEOUT seconds."""
    while _server_running:
        time.sleep(5)
        if _last_request_time > 0:
            idle_time = time.time() - _last_request_time
            if idle_time > IDLE_TIMEOUT:
                _stop_odoo_containers()
                os._exit(0)

# In main:
idle_thread = threading.Thread(target=_check_idle_and_exit, daemon=True)
idle_thread.start()
```

Each MCP tool now calls `_update_activity()` to reset the idle timer.

---

### Problem 5: Email Approval Not Required for Invoice Flow

**Issue:** Every email reply required manual approval, but invoice confirmations are safe (draft only, no money moves).

**Solution:**
1. Updated Company_Handbook.md with Auto-Approved rules:
   - Invoice confirmation emails auto-approved
   - Draft invoices auto-approved
   - Archive/no-action emails auto-approved

2. Updated email_responder skill:
   - Invoice requests skip Pending_Approval/
   - Reply sent directly via send_email_tool
   - `requires_approval: false` in plan

---

### Problem 6: Token Expired - Gmail Authorization

**Issue:** `invalid_grant: Token has been expired or revoked.`

**Solution:** Re-authorize:
```bash
uv run python -m src.main gmail --authorize
```

Note: Google OAuth tokens expire (refresh tokens can expire after 6 months of inactivity).

---

## Configuration Summary

### .env Key Variables
```env
# Watchers
POLL_INTERVAL=60

# Orchestrator
CLAUDE_TIMEOUT=600
DRY_RUN=false

# Gmail
GMAIL_CREDENTIALS_PATH=.secrets/gmail_credentials.json
GMAIL_TOKEN_PATH=.secrets/gmail_token.json
GMAIL_QUERY=is:unread

# Odoo
ODOO_URL=http://localhost:8069
ODOO_DB=fte-ai-employee
ODOO_USER=admin
ODOO_PASSWORD=admin

# MCP Server
MCP_IDLE_TIMEOUT=30
```

---

## Testing the Flow

### Prerequisites
1. Odoo Docker containers configured
2. Gmail OAuth2 credentials
3. DRY_RUN=false in .env

### Step-by-Step Test

1. **Start the system:**
   ```bash
   uv run python -m src.main run
   ```

2. **Send a test email:**
   - From any email account
   - To your configured Gmail
   - Subject: "Invoice Request - [Project Name]"
   - Body: Include line items with PKR amounts

3. **Watch the flow:**
   - Gmail watcher detects email (check logs)
   - EMAIL_*.md created in Needs_Action/
   - Orchestrator picks up file
   - Claude subprocess runs
   - Invoice created in Odoo
   - Reply email sent
   - Summary written to Done/

4. **Verify:**
   - Odoo: New invoice in Draft status
   - Gmail: Reply received in inbox
   - Vault: Summary file in Done/
   - Docker: Containers stop after ~30s idle

---

## Files Modified

| File | Change |
|------|--------|
| src/orchestrator/orchestrator.py | cwd fixed to project_root |
| src/main.py | GMAIL_CREDENTIALS_PATH check |
| src/watchers/gmail_watcher.py | Query changed to is:unread |
| src/mcp/odoo_server.py | Idle timeout + auto-stop |
| AI_Employee_Vault/Company_Handbook.md | Auto-approve rules added |
| .claude/skills/email_responder.md | Cross-domain flow + auto-approve |
| .env | Added GMAIL_CREDENTIALS_PATH, MCP_IDLE_TIMEOUT |

---

## Key Success Metrics

| Feature | Status |
|---------|--------|
| Gmail → Email file | ✅ Working |
| Orchestrator → Claude subprocess | ✅ Working |
| Claude → MCP tools | ✅ Working |
| Odoo invoice creation | ✅ Working |
| Reply email sent | ✅ Working |
| Auto-approve | ✅ Working |
| Auto-stop containers | ✅ Working (30s idle) |

---

## Known Limitations

1. **WhatsApp Watcher:** Requires Playwright browser, may fail in headless environments
2. **Social Media:** Facebook, Instagram, Twitter, LinkedIn MCP servers configured but not fully tested
3. **Token Expiry:** Gmail tokens need re-authorization periodically
4. **CEO Briefing:** Code exists but scheduled job not tested yet

---

## Gold Tier Requirements vs Implementation (from PDF)

### From PDF (Page 4) — Gold Tier Requirements:

| Requirement | Implementation Status |
|-------------|---------------------|
| Full cross-domain integration (Personal + Business) | ✅ Done (Email→Odoo) |
| Odoo Community + MCP JSON-RPC (Odoo 19+) | ✅ Done |
| Facebook + Instagram integration | ⚠️ MCP code exists, not tested |
| Twitter (X) integration | ⚠️ MCP code exists, not tested |
| Multiple MCP servers | ✅ 6 servers configured |
| Weekly CEO Briefing | ⚠️ Code exists, not tested |
| Error recovery | ⚠️ Basic implementation |
| Audit logging | ✅ Done |
| Ralph Wiggum loop | ✅ Done (Stop hook) |
| Documentation | ✅ This file |
| Agent Skills | ✅ Done |

### Silver Tier Requirements (included in Gold):

| Requirement | Status |
|-------------|--------|
| Gmail Watcher | ✅ Done |
| WhatsApp Watcher | ⚠️ Playwright issue |
| LinkedIn automation | ⚠️ Code exists |
| Plan.md creation | ✅ Done |
| Email MCP | ✅ Done |
| Human-in-the-loop approval | ✅ Done |
| Scheduling (cron) | ⚠️ APScheduler configured |

---

## References

- MCP Server: `src/mcp/odoo_server.py`
- Orchestrator: `src/orchestrator/orchestrator.py`
- Email Responder: `.claude/skills/email_responder.md`
- Company Handbook: `AI_Employee_Vault/Company_Handbook.md`
