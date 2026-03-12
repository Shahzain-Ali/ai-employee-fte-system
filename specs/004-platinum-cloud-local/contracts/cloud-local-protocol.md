# Cloud-Local Communication Protocol

**Feature**: 004-platinum-cloud-local
**Date**: 2026-03-09

---

## Overview

Cloud and Local agents communicate exclusively through files in the Git-synced vault.
There is NO direct network communication between agents. All coordination happens
through file presence, file location, and file content.

---

## Protocol: Task Lifecycle

### 1. Task Creation (Cloud → Vault)

```
Trigger: Watcher detects event (email, social, invoice)
Action:  Cloud creates task file in /Needs_Action/<domain>/
Sync:    gitwatch auto-commits + pushes to GitHub
```

**File format**: See data-model.md → Task File entity

### 2. Task Claim (Agent → Vault)

```
Check:   Agent scans /Needs_Action/<domain>/ for unclaimed files
Action:  MOVE file to /In_Progress/<agent>/
Sync:    gitwatch auto-commits + pushes
Rule:    First agent to complete the move owns the task (claim-by-move)
```

### 3. Draft Creation (Cloud → Vault)

```
Action:  Cloud Agent processes task, creates draft
Output:  MOVE file to /Pending_Approval/<domain>/
Content: Task file updated with draft content in body
Sync:    gitwatch auto-commits + pushes
```

### 4. Approval (Local → Vault)

```
Check:   Local Agent scans /Pending_Approval/ after git pull
Display: Present draft to owner for review
Options: Approve | Reject | Edit
```

**On Approve:**
```
Action:  Local Agent executes final action (send email, publish post, etc.)
Output:  MOVE file to /Done/<domain>/
Sync:    gitwatch auto-commits + pushes
```

**On Reject:**
```
Action:  MOVE file to /Done/<domain>/ with status: rejected in frontmatter
Sync:    gitwatch auto-commits + pushes
```

### 5. Status Reporting (Cloud → Vault)

```
Frequency: After each batch of actions or every 30 minutes
Action:    Cloud writes /Updates/cloud_status_<timestamp>.md
Content:   Actions taken, pending approvals, alerts
Sync:      gitwatch auto-commits + pushes
```

### 6. Dashboard Update (Local only)

```
Trigger:  Local Agent reads /Updates/ files after git pull
Action:   Merge updates into Dashboard.md
Rule:     ONLY Local Agent writes Dashboard.md (single-writer)
```

---

## Protocol: Git Sync

### Push (event-based via gitwatch)

```
1. File change detected by inotifywait
2. Wait 2 seconds (debounce)
3. git add -A
4. git commit -m "auto: <agent> <timestamp>"
5. git push origin main
```

### Pull (timer-based via cron)

```
1. Every 2-3 minutes (cron)
2. git pull --rebase origin main
3. On conflict: git pull --rebase --strategy-option=theirs
4. Log result
```

### Conflict Resolution

| File Type | Strategy | Rationale |
|-----------|----------|-----------|
| Task files in /Needs_Action/ | Accept remote (theirs) | Claim-by-move resolves ownership |
| Task files in /In_Progress/ | Accept remote (theirs) | First mover already owns it |
| Log files | Accept both (concatenate) | Logs are append-only |
| Updates/ files | Accept remote (theirs) | Each update has unique timestamp filename |
| Dashboard.md | Accept local (ours) | Single-writer rule: Local owns it |

---

## Protocol: Model Selection (Token Efficiency)

```
For each task:
1. Assess complexity: routine (triage, simple draft) vs complex (multi-step reasoning)
2. Select model:
   - Routine tasks: claude-sonnet-4-6 (fast, token-efficient)
   - Complex tasks: claude-opus-4-6 (deep reasoning)
   - Fallback (paid limit exhausted): minimax:m2.5:cloud via Ollama
3. Pass model flag: claude -p "prompt" --model <selected-model>
   Or via SDK: query(prompt, model=<selected-model>)
```

---

## Protocol: Health Monitoring

```
Every 3-5 minutes (cron on Cloud VM):
1. Check Odoo: curl -s -o /dev/null -w "%{http_code}" http://localhost:8069
2. Check processes: pgrep -f "gmail_watcher|orchestrator"
3. Check disk: df -h / | awk 'NR==2 {print $5}'
4. Check RAM: free -m | awk 'NR==2 {print $3/$2 * 100}'
5. Check last git push: stat -c %Y /path/to/vault/.git/refs/remotes/origin/main

On failure:
- Attempt restart (pm2 restart <process>)
- If 3 restarts fail: write alert to /Updates/alert_<timestamp>.md
- Alert syncs to Local via git push → Local notifies owner
```

---

## API Contracts: MCP Server URL Changes

### Odoo MCP (fte-odoo)

**Gold Tier (current):**
```json
{ "ODOO_URL": "http://localhost:8069" }
```

**Platinum Tier (cloud):**
```json
{ "ODOO_URL": "https://odoo.yourdomain.com" }
```

All other MCP tool signatures remain UNCHANGED. Only the base URL changes.

### Email MCP (fte-email)

No URL change needed — Gmail API is cloud-based.
Both Cloud and Local use same Gmail API credentials.
**But**: Cloud MUST NOT call `send_email_tool` — only `draft_email_tool`.

### Social Media MCPs (fte-facebook, fte-instagram, fte-twitter, fte-linkedin)

No URL change needed — Meta/Twitter APIs are cloud-based.
**But**: Cloud MUST NOT call `create_page_post`, `create_ig_post`, `post_tweet` — only read operations.
