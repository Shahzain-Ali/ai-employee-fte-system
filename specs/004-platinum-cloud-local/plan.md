# Implementation Plan: Platinum Tier — Always-On Cloud + Local Executive

**Branch**: `004-platinum-cloud-local` | **Date**: 2026-03-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-platinum-cloud-local/spec.md`

## Summary

Deploy the AI Employee system on Oracle Cloud Free Tier ARM A1 VM (4 OCPUs, 24GB RAM)
running 24/7, while the owner's laptop acts as the approval and sensitive-action executor.
Cloud and Local agents communicate via a Git-synced vault (GitHub as intermediary) using
gitwatch (event-based push) + cron (timer-based pull). Work-Zone Specialization enforces
that Cloud only creates drafts while Local handles all final actions (send, publish,
approve). Odoo migrates to cloud with HTTPS via Let's Encrypt + Nginx. Health monitoring
auto-restarts failed components. Token efficiency achieved via Sonnet for routine tasks,
Opus for complex reasoning, and Ollama fallback (minimax:m2.5:cloud) when paid limits
are exhausted.

## Technical Context

**Language/Version**: Python 3.12+ (managed via `uv`) + Bash scripts + Node.js 22 LTS (for Claude Code CLI)
**Primary Dependencies**: claude-agent-sdk (Python), gitwatch + inotify-tools (sync), PM2 (process mgmt), Nginx + certbot (HTTPS), Docker (Odoo)
**Storage**: Git repository (vault), PostgreSQL (Odoo), JSON files (logs), Markdown files (tasks/drafts)
**Testing**: Manual end-to-end (Platinum Demo), health check scripts, audit log verification
**Target Platform**: Oracle Cloud ARM A1 (Ubuntu 22.04 aarch64) + Windows WSL2 (Local)
**Project Type**: Single project — distributed deployment (Cloud + Local)
**Performance Goals**: Vault sync < 5 minutes, draft creation < 2 minutes, health recovery < 5 minutes
**Constraints**: Oracle Free Tier limits (4 OCPU, 24GB RAM, 200GB disk, 50Mbps), zero ongoing cost
**Scale/Scope**: Single user (owner), 2 agents (Cloud + Local), 6 MCP servers, ~50 vault files/day max

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-First Architecture | **PASS** | Sensitive data (WhatsApp, banking, credentials) stays LOCAL only. Cloud has limited `.env`. Vault syncs only markdown/JSON. |
| II. Human-in-the-Loop (HITL) | **PASS** | Cloud creates drafts → Local requires owner approval → then executes. No autonomous sensitive actions. |
| III. Agent Skills First | **PASS** | Existing 14 Agent Skills preserved. New skills added for cloud-orchestrator and local-orchestrator. |
| IV. Documentation-First Development | **PASS** | Full spec → research → plan → tasks workflow followed. |
| V. Security by Design | **PASS** | `.gitignore` before first sync. Independent `.env` files. SSH key-only. fail2ban. No secrets in vault. |
| VI. Tiered Complexity Growth | **PASS** | Gold Tier fully complete. Platinum adds only Cloud/Local split on top. |

**Post-Design Re-Check:**

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-First | **PASS** | Data model enforces credential split. Cloud `.env` has no WhatsApp/banking. |
| II. HITL | **PASS** | Cloud-Local protocol requires Pending_Approval flow for all actions. |
| III. Agent Skills | **PASS** | New skills: `cloud_orchestrator.md`, `local_orchestrator.md`, `vault_sync.md`. |
| V. Security | **PASS** | `.gitignore` configured in quickstart Phase 2.3 BEFORE any sync. |

## Project Structure

### Documentation (this feature)

```text
specs/004-platinum-cloud-local/
├── spec.md                    # Feature specification
├── plan.md                    # This file
├── research.md                # Phase 0: Technology research
├── data-model.md              # Phase 1: Vault structure, entities
├── quickstart.md              # Phase 1: Setup guide
├── contracts/
│   └── cloud-local-protocol.md  # Phase 1: Agent communication protocol
├── checklists/
│   └── requirements.md        # FR/SC tracking checklist
└── tasks.md                   # Phase 2: Implementation tasks (via /sp.tasks)
```

### Source Code (repository root)

```text
src/
├── orchestrator/
│   ├── orchestrator.py           # EXISTING — base orchestrator (Gold)
│   ├── cloud_orchestrator.py     # NEW — Cloud-specific orchestrator
│   ├── local_orchestrator.py     # NEW — Local-specific orchestrator
│   ├── vault_manager.py          # NEW — Vault folder operations (claim-by-move, etc.)
│   ├── model_selector.py         # NEW — Sonnet/Opus/Ollama model selection
│   ├── approval_handler.py       # EXISTING — approval workflow
│   ├── approval_watcher.py       # EXISTING — watches approval files
│   ├── component_health.py       # EXISTING — health checks
│   └── workflow_engine.py        # EXISTING — workflow execution
├── watchers/
│   ├── gmail_watcher.py          # EXISTING — deployed on Cloud
│   ├── whatsapp_watcher.py       # EXISTING — stays on Local only
│   ├── filesystem_watcher.py     # EXISTING — vault file watching
│   └── base_watcher.py           # EXISTING
├── mcp/
│   ├── email_server.py           # EXISTING — both Cloud (draft) + Local (send)
│   ├── odoo_server.py            # EXISTING — URL change to cloud HTTPS
│   ├── facebook_server.py        # EXISTING — Cloud (read) + Local (post)
│   ├── instagram_server.py       # EXISTING — Cloud (read) + Local (post)
│   ├── twitter_server.py         # EXISTING
│   └── linkedin_server.py        # EXISTING
├── sync/
│   └── git_sync.py               # NEW — Git sync management (push/pull status)
├── health/
│   └── health_monitor.py         # NEW — Cloud health monitoring script
├── dashboard/
│   └── app.py                    # EXISTING
└── utils/
    └── (existing utils)

scripts/
├── ralph-wiggum-check.sh         # EXISTING
├── run-dashboard.sh              # EXISTING
├── setup-cloud-vm.sh             # NEW — Cloud VM provisioning automation
├── start-cloud.sh                # NEW — Cloud agent startup script
├── start-local.sh                # NEW — Local agent startup script (WSL auto-start)
├── health-monitor.sh             # NEW — Health check script (cron)
└── backup-odoo.sh                # NEW — Odoo database backup script

config/
├── cloud-agent.yaml              # NEW — Cloud Agent zone permissions
├── local-agent.yaml              # NEW — Local Agent zone permissions
├── ecosystem.config.js           # NEW — PM2 process configuration
└── nginx-odoo.conf               # NEW — Nginx reverse proxy config for Odoo

.claude/skills/
├── cloud_orchestrator.md         # NEW — Cloud Agent behavior + zone rules
├── local_orchestrator.md         # NEW — Local Agent behavior + zone rules
├── vault_sync_manager.md         # NEW — Vault sync and conflict resolution
├── (existing 14 skills)          # PRESERVED from Gold Tier
```

**Structure Decision**: Single project with distributed deployment. The same codebase
deploys to both Cloud and Local, with agent-specific configs (`cloud-agent.yaml` vs
`local-agent.yaml`) controlling zone permissions and behavior. No separate repos needed.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           ORACLE CLOUD VM (24/7)        │
│                                          │
│  ┌──────────┐  ┌──────────────────────┐ │
│  │ Watchers  │  │  Cloud Orchestrator  │ │
│  │ (Gmail,   │→│  (draft-only zone)   │ │
│  │  Social)  │  │                      │ │
│  └──────────┘  │  ┌────────────────┐  │ │
│                 │  │ Claude Code    │  │ │
│  ┌──────────┐  │  │ (Sonnet/Opus)  │  │ │
│  │ Odoo     │  │  │ via Agent SDK  │  │ │
│  │ (Docker) │  │  └────────────────┘  │ │
│  │ + HTTPS  │  └──────────────────────┘ │
│  └──────────┘                            │
│         │                                │
│  ┌──────────┐  ┌──────────────────────┐ │
│  │ Health   │  │ gitwatch (push)      │ │
│  │ Monitor  │  │ cron pull (3min)     │ │
│  └──────────┘  └──────────┬───────────┘ │
└─────────────────────────────┼────────────┘
                              │ Git push/pull
                    ┌─────────┴─────────┐
                    │   GitHub (Private  │
                    │   Repository)      │
                    └─────────┬─────────┘
                              │ Git push/pull
┌─────────────────────────────┼────────────┐
│       LOCAL LAPTOP (WSL2)   │            │
│                              │            │
│  ┌──────────────────────────┴──────────┐ │
│  │ gitwatch (push) + cron pull (3min)  │ │
│  └──────────────────────────┬──────────┘ │
│                              │            │
│  ┌──────────────────────────────────────┐│
│  │  Local Orchestrator (full zone)      ││
│  │  ┌────────────┐ ┌────────────────┐   ││
│  │  │ Approval   │ │ Claude Code    │   ││
│  │  │ Handler    │ │ (Sonnet/Opus)  │   ││
│  │  └────────────┘ └────────────────┘   ││
│  │                                       ││
│  │  MCP Servers: email(send), social     ││
│  │  (publish), odoo(confirm)             ││
│  └──────────────────────────────────────┘│
│                                           │
│  ┌──────────────┐  ┌──────────────────┐  │
│  │ WhatsApp     │  │ Dashboard.md     │  │
│  │ (Local only) │  │ (single-writer)  │  │
│  └──────────────┘  └──────────────────┘  │
└───────────────────────────────────────────┘
```

## Implementation Phases

### Phase A: Cloud VM Infrastructure (P2, P5)
1. Provision Oracle Cloud ARM A1 VM
2. Install all dependencies (Docker, Node.js, Python, uv, PM2, Nginx)
3. Configure SSH security (key-only, fail2ban)
4. Create vault GitHub repo with `.gitignore` (security-first)
5. Set up vault folder structure
6. Install and configure gitwatch + cron pull on Cloud

### Phase B: Vault Sync & Data Model (P4)
1. Implement vault_manager.py (claim-by-move, file operations)
2. Implement git_sync.py (sync status monitoring)
3. Set up gitwatch + cron pull on Local (WSL)
4. Test bidirectional sync: Cloud → GitHub → Local and vice versa
5. Test claim-by-move conflict resolution

### Phase C: Agent Zone Split (P3)
1. Create cloud-agent.yaml and local-agent.yaml configs
2. Implement cloud_orchestrator.py (draft-only zone enforcement)
3. Implement local_orchestrator.py (full zone + approval handling)
4. Implement model_selector.py (Sonnet/Opus/Ollama selection)
5. Create Agent Skills: cloud_orchestrator.md, local_orchestrator.md
6. Test: Cloud cannot send/publish; Local can

### Phase D: Odoo on Cloud (P6)
1. Deploy Odoo via Docker (arm64v8/odoo) on Cloud VM
2. Configure Nginx reverse proxy
3. Set up Let's Encrypt HTTPS (certbot)
4. Update Odoo MCP server URL to cloud HTTPS
5. Configure daily backup cron
6. Test Odoo MCP operations via HTTPS from both Cloud and Local

### Phase E: Health Monitoring & Auto-Start (P7, P8)
1. Implement health_monitor.py / health-monitor.sh
2. Configure PM2 ecosystem for all Cloud processes
3. Set up `pm2 startup` for reboot persistence
4. Configure Windows Task Scheduler for Local auto-start
5. Create start-local.sh script
6. Test: Kill process → verify auto-restart; Reboot VM → verify auto-start

### Phase F: Platinum Demo (P1)
1. End-to-end integration test
2. Send email while laptop is OFF
3. Verify Cloud drafts reply
4. Verify sync to Local
5. Verify approval flow
6. Verify email sent
7. Verify logging and task completion
8. Document demo script for hackathon judges

## Model Selection Strategy

Per user requirement, token-efficient model selection:

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| Email triage, simple drafts | `claude-sonnet-4-6` | Fast, cheap, sufficient for routine |
| Complex reasoning, multi-step | `claude-opus-4-6` | Deep analysis needed |
| Paid limit exhausted | `minimax:m2.5:cloud` via Ollama | Free fallback, local inference |

**Implementation**: `model_selector.py` checks task complexity and API quota before
selecting model. Pass `--model` flag to `claude -p` or `model` param to Agent SDK.

**Ollama Fallback Setup:**
```bash
# On both Cloud VM and Local
curl -fsSL https://ollama.com/install.sh | sh
ollama pull minimax:m2.5:cloud
# Claude Code: claude --model ollama:minimax:m2.5:cloud -p "prompt"
```

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Oracle A1 "Out of capacity" | Cannot provision VM | Try different regions; retry at off-peak hours |
| ARM64 Claude Code auth issues | Cannot run AI on cloud | Use claude-agent-sdk (bundles CLI); copy auth from x86 |
| Git merge conflicts | Lost or duplicate work | Claim-by-move rule + auto-resolve strategies per file type |
| GitHub outage | Sync stops | Both agents continue locally; queue pushes for reconnection |
| Let's Encrypt rate limits | Cannot get HTTPS cert | Use staging environment first; self-signed cert as fallback |
| API token exhaustion | No AI processing | Ollama fallback (minimax:m2.5:cloud) for continued operation |
| Odoo ARM64 Docker issues | No accounting on cloud | Use official arm64v8/odoo image (verified available) |

## Complexity Tracking

No constitution violations. All complexity is justified by the Platinum Tier requirements.

| Addition | Why Needed | Simpler Alternative Rejected Because |
|----------|-----------|-------------------------------------|
| Two orchestrators (cloud + local) | Zone enforcement requires different permission sets | Single orchestrator cannot enforce zone split |
| gitwatch + cron | Bidirectional sync needed | Manual git push/pull is not 24/7 compatible |
| PM2 ecosystem | Multiple processes need management | Manual restart is not 24/7 compatible |
| Model selector | Token cost optimization (user requirement) | Always using Opus wastes budget on routine tasks |

---

## Generated Artifacts

- [research.md](./research.md) — Phase 0: Technology research (6 research items)
- [data-model.md](./data-model.md) — Phase 1: Vault structure, entities, configs
- [contracts/cloud-local-protocol.md](./contracts/cloud-local-protocol.md) — Phase 1: Agent communication protocol
- [quickstart.md](./quickstart.md) — Phase 1: Step-by-step setup guide

**Next Step**: Run `/sp.tasks` to generate implementation task list.
