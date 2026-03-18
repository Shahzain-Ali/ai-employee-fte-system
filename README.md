# FTE AI Employee

> **Your life and business on autopilot.** Local-first, agent-driven, human-in-the-loop.

An autonomous AI agent that manages your personal and business affairs 24/7. It reads your Gmail, monitors WhatsApp, posts on social media, creates invoices in Odoo, and generates weekly CEO Briefings — all while keeping you in control through a human-approval workflow.

**Tier: Gold (Autonomous Employee)** | **Platinum: In Progress**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Environment Variables](#environment-variables)
5. [Integration Setup](#integration-setup)
   - [Gmail API](#1-gmail-api)
   - [Facebook + Instagram (Meta API)](#2-facebook--instagram-meta-api)
   - [LinkedIn](#3-linkedin)
   - [Twitter/X](#4-twitterx)
   - [Odoo Accounting](#5-odoo-accounting-docker)
   - [WhatsApp](#6-whatsapp)
6. [Running the System](#running-the-system)
   - [All Commands](#all-commands)
7. [Dashboard](#dashboard)
8. [MCP Servers (28 Tools)](#mcp-servers-28-tools)
9. [Agent Skills (17 Skills)](#agent-skills-17-skills)
10. [Security](#security)
11. [Tier Checklist](#tier-checklist)
    - [Bronze Tier](#bronze-tier-foundation-)
    - [Silver Tier](#silver-tier-functional-assistant-)
    - [Gold Tier](#gold-tier-autonomous-employee-)
    - [Platinum Tier (Roadmap)](#platinum-tier-always-on-cloud--local-)
12. [Project Structure](#project-structure)
13. [Troubleshooting](#troubleshooting)
14. [Demo Video](#demo-video)
15. [Credits](#credits)

---

## Overview

A **Digital FTE (Full-Time Equivalent)** — an AI agent built, "hired," and priced as if it were a human employee.

**What it does:**
- Reads Gmail and drafts professional replies
- Monitors WhatsApp for urgent business keywords (invoice, payment, urgent, etc.)
- Posts on Facebook, Instagram, Twitter/X, and LinkedIn
- Creates invoices and tracks payments in Odoo
- Generates weekly CEO Briefings with financial and social media metrics
- Logs every action for audit compliance

**Human FTE vs Digital FTE:**

| | Human | Digital FTE |
|---|---|---|
| **Availability** | 40 hrs/week | 168 hrs/week (24/7) |
| **Monthly Cost** | $4,000 – $8,000+ | $500 – $2,000 |
| **Ramp-up** | 3 – 6 months | Instant (via Agent Skills) |
| **Cost per Task** | ~$3.00 – $6.00 | ~$0.25 – $0.50 |
| **Annual Hours** | ~2,000 | ~8,760 |

---

## Architecture

The system follows a **Perception → Reasoning → Action** pipeline:

```
┌──────────────────────────────────────────────────────────────┐
│                      EXTERNAL SOURCES                        │
│  Gmail │ WhatsApp │ Facebook │ Instagram │ Twitter │ LinkedIn│
└────┬───┴────┬─────┴────┬─────┴─────┬─────┴────┬────┴────┬───┘
     ▼        ▼          ▼           ▼          ▼         ▼
┌──────────────────────────────────────────────────────────────┐
│  PERCEPTION LAYER (Watchers)                                 │
│  Gmail Watcher (OAuth2) │ WhatsApp Watcher (Playwright)      │
│  Filesystem Watcher (watchdog)                               │
│  Output: EMAIL_*.md / WA_*.md → /Needs_Action/              │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  OBSIDIAN VAULT (Local Knowledge Base)                       │
│                                                              │
│  /Needs_Action/  → Incoming tasks from watchers              │
│  /Plans/         → Claude's reasoning scratchpads            │
│  /Pending_Approval/ → Awaiting human review                  │
│  /Approved/      → Human-approved, ready to execute          │
│  /Done/          → Completed tasks                           │
│  /Logs/          → JSON audit trail (YYYY-MM-DD.json)        │
│  /Briefings/     → CEO briefing reports                      │
│                                                              │
│  Dashboard.md │ Company_Handbook.md                          │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  REASONING LAYER (Claude Code + 17 Agent Skills)             │
│  Read → Think → Plan → Write → Request Approval             │
│  Ralph Wiggum Loop: keeps iterating until task is complete   │
└─────────┬────────────────────────────────┬───────────────────┘
          ▼                                ▼
┌───────────────────────┐   ┌──────────────────────────────────┐
│  HUMAN-IN-THE-LOOP    │   │  ACTION LAYER (6 MCP Servers)    │
│                       │   │                                  │
│  Review in Obsidian   │──>│  fte-email     (2 tools)         │
│  Move to /Approved/   │   │  fte-odoo      (6 tools)         │
│  or /Rejected/        │   │  fte-facebook  (5 tools)         │
└───────────────────────┘   │  fte-instagram (6 tools)         │
                            │  fte-twitter   (4 tools)         │
                            │  fte-linkedin  (5 tools)         │
                            │                                  │
                            │  Total: 28 tools                 │
                            └──────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────┐
│  ORCHESTRATION LAYER                                         │
│  orchestrator.py │ APScheduler │ Audit Logger │ Retry Logic  │
└──────────────────────────────────────────────────────────────┘
```

**Design Principles:**
- **Human-in-the-Loop (HITL)** — Sensitive actions (payments, emails, social posts) require explicit human approval
- **Ralph Wiggum Loop** — A stop hook pattern that keeps Claude iterating until multi-step tasks are complete
- **File-Based Communication** — Agents coordinate through markdown files in the Obsidian vault
- **Graceful Degradation** — If a service is down (Odoo, Gmail, etc.), the system continues working with available services

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Reasoning Engine | Claude Code (Opus 4.6) | Latest |
| Knowledge Base | Obsidian (local Markdown) | v1.10.6+ |
| Language | Python | 3.12+ (managed via `uv`) |
| MCP Email Server | Node.js | v22+ LTS |
| Package Manager | uv | Latest |
| Web Dashboard | Streamlit | Latest |
| Accounting | Odoo 17 Community (Docker) | 17.0 |
| Database (Odoo) | PostgreSQL (Docker) | 15 |
| Social Media APIs | Meta Graph API | v21.0 |
| Browser Automation | Playwright | Latest |
| Scheduling | APScheduler + SQLAlchemy | Latest |
| Process Management | PM2 (Platinum tier) | Latest |

---

## Getting Started

### Prerequisites

| Software | Required | Purpose |
|----------|----------|---------|
| Claude Code | Active subscription | AI reasoning engine |
| Python | 3.12+ | Core system |
| Node.js | v22+ LTS | Email MCP server |
| uv | Latest | Python package manager |
| Obsidian | v1.10.6+ (free) | Vault GUI |
| Docker Desktop | Latest | Odoo accounting (Gold tier) |
| Git | Latest | Version control |

**Hardware**: 8GB+ RAM, 4-core CPU, 20GB disk, 10+ Mbps internet.

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/full-time-equivalent-project.git
cd full-time-equivalent-project

# Install Python dependencies
uv sync

# Install Node.js dependencies (email MCP server)
cd src/mcp && npm install && cd ../..

# Install Playwright browsers (WhatsApp, Twitter, LinkedIn automation)
uv run playwright install chromium

# Initialize vault structure (creates all folders + core files)
uv run python -m src.main setup
```

After setup, open Obsidian → Open folder → select `AI_Employee_Vault/`.

### Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values. All variables are documented in `.env.example`:

| Variable | Tier | Description |
|----------|------|-------------|
| `VAULT_PATH` | Bronze | Path to Obsidian vault (default: `./AI_Employee_Vault`) |
| `POLL_INTERVAL` | Bronze | Watcher poll interval in seconds (default: `60`) |
| `CLAUDE_TIMEOUT` | Bronze | Max AI task duration in seconds (default: `300`) |
| `DRY_RUN` | Bronze | `true` = testing mode, `false` = production |
| `LOG_LEVEL` | Bronze | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `GMAIL_CREDENTIALS_PATH` | Silver | Path to Gmail OAuth credentials (default: `.secrets/gmail_credentials.json`) |
| `GMAIL_TOKEN_PATH` | Silver | Path to Gmail token (default: `.secrets/gmail_token.json`) |
| `LINKEDIN_ACCESS_TOKEN` | Silver | LinkedIn OAuth2 access token |
| `LINKEDIN_PERSON_URN` | Silver | Your LinkedIn Person URN (e.g., `urn:li:person:abc123`) |
| `WHATSAPP_SESSION_PATH` | Silver | Playwright session directory (default: `.sessions/whatsapp`) |
| `ODOO_URL` | Gold | Odoo server URL (default: `http://localhost:8069`) |
| `ODOO_DB` | Gold | Odoo database name (default: `fte-ai-employee`) |
| `ODOO_USER` | Gold | Odoo username (default: `admin`) |
| `ODOO_PASSWORD` | Gold | Odoo password |
| `FB_PAGE_ID` | Gold | Facebook Page ID |
| `FB_PAGE_ACCESS_TOKEN` | Gold | Facebook Page Access Token |
| `IG_USER_ID` | Gold | Instagram Business/Creator User ID |
| `IG_ACCESS_TOKEN` | Gold | Instagram Access Token |
| `META_API_VERSION` | Gold | Meta Graph API version (default: `v21.0`) |
| `OWNER_EMAIL` | Gold | Email address for CEO Briefing delivery |
| `RALPH_WIGGUM_MAX_ITERATIONS` | Gold | Max autonomous loop iterations (default: `10`) |

> **SECURITY**: `.env` and `.secrets/` are in `.gitignore` — never committed to git.

---

## Integration Setup

Each integration is optional. Set up only what you need.

### 1. Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → Create project → Enable **Gmail API**
2. Create OAuth 2.0 credentials (Desktop App type)
3. Download JSON → save as `.secrets/gmail_credentials.json`
4. Authorize:
   ```bash
   uv run python -m src.main gmail --authorize
   ```
5. Token saves to `.secrets/gmail_token.json` (auto-refreshes on expiry)

> Detailed guide: `Learning/Gmail_API_Setup_Guide.md`

### 2. Facebook + Instagram (Meta API)

1. Create a Facebook Page → Go to [Meta for Developers](https://developers.facebook.com/)
2. Create app (Business type) → Add **Facebook Login** + **Instagram Graph API** products
3. Generate Page Access Token with permissions:
   - `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`
   - `instagram_basic`, `instagram_content_publish`, `instagram_manage_comments`
4. Find your Page ID and Instagram User ID → Add to `.env`

> Detailed guide: `Learning/Meta_API_Facebook_Instagram_Setup_Guide.md`

### 3. LinkedIn

1. Create LinkedIn Page → Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create app → Verify with LinkedIn Page
3. Request products: **Share on LinkedIn**, **Sign In with LinkedIn using OpenID Connect**
4. Generate access token (scopes: `openid`, `profile`, `w_member_social`)
5. Find Person URN → Add to `.env`

> Detailed guide: `Learning/LinkedIn_API_Setup_Guide.md`

### 4. Twitter/X

Uses Playwright browser automation. First-time login:

```bash
uv run python -c "
from src.playwright.twitter_bot import TwitterBot
import asyncio
asyncio.run(TwitterBot().login())
"
```

Log into your Twitter/X account in the browser window. Session saves to `.sessions/twitter/`.

### 5. Odoo Accounting (Docker)

```bash
# Start Odoo + PostgreSQL
docker-compose -f config/docker-compose-odoo.yml up -d
```

Wait 60 seconds, then open `http://localhost:8069`:
- Database Name: `fte-ai-employee`
- Email: `admin`
- Password: `admin`

After creation, install the **Invoicing** module inside Odoo.

### 6. WhatsApp

```bash
uv run python -m src.main whatsapp --setup
```

Scan the QR code with your phone. Session saves to `.sessions/whatsapp/`.

---

## Running the System

```bash
# Terminal 1 — Start AI Employee (all watchers + orchestrator)
uv run python -m src.main run

# Terminal 2 — Start web dashboard
uv run python -m src.main dashboard
```

Dashboard opens at **http://localhost:8501**.

### All Commands

| Command | Description |
|---------|-------------|
| `uv run python -m src.main setup` | Initialize vault structure and core files |
| `uv run python -m src.main run` | Start all watchers + orchestrator |
| `uv run python -m src.main gmail --authorize` | First-time Gmail OAuth2 setup |
| `uv run python -m src.main gmail --once` | Run one Gmail check and exit |
| `uv run python -m src.main gmail --start` | Run Gmail watcher continuously |
| `uv run python -m src.main whatsapp --setup` | First-time WhatsApp QR code scan |
| `uv run python -m src.main whatsapp --once` | Run one WhatsApp check and exit |
| `uv run python -m src.main whatsapp --start` | Run WhatsApp watcher continuously |
| `uv run python -m src.main briefing` | Generate CEO Briefing for current week |
| `uv run python -m src.main briefing 2026-03-10` | Generate briefing for specific week |
| `uv run python -m src.main dashboard` | Start Streamlit web dashboard |
| `uv run python -m src.main help` | Show all available commands |

---

## Dashboard

Streamlit web dashboard with 7 sections:

| Section | Description |
|---------|-------------|
| **Overview** | System health, active watchers, recent activity, pending items |
| **Finance** | Odoo connection status, weekly revenue/outstanding/pending, invoice table with filters |
| **Social Media** | Facebook page posts + insights, Instagram media + insights, Twitter feed, LinkedIn posts |
| **Communications** | Send test emails via Gmail API, view email status |
| **CEO Briefing** | View past briefings, download as PDF, email to stakeholders, generate new briefing |
| **Settings** | System config (DRY_RUN, timeouts), Docker/Odoo status, MCP server status, approval rules |
| **Logs** | Activity logs with date filter, action type filter, expandable JSON details |

---

## MCP Servers (28 Tools)

6 MCP servers configured in `.mcp.json`:

### fte-email — Node.js (`src/mcp/index.js`)
| Tool | Description |
|------|-------------|
| `send_email_tool` | Send email via Gmail API |
| `draft_email_tool` | Preview email without sending |

### fte-odoo — Python (`src/mcp/odoo_server.py`)
| Tool | Description |
|------|-------------|
| `create_invoice` | Create draft invoice in Odoo |
| `get_invoices` | List invoices with filters |
| `mark_payment_received` | Record payment on invoice |
| `get_weekly_summary` | Revenue, expenses, outstanding balance |
| `get_expenses` | List expense records |
| `create_expense` | Create new expense entry |

### fte-facebook — Python (`src/mcp/facebook_server.py`)
| Tool | Description |
|------|-------------|
| `create_page_post` | Publish post to Facebook Page |
| `get_page_posts` | List recent page posts |
| `get_post_comments` | Read comments on a post |
| `reply_to_comment` | Reply to a comment |
| `get_page_insights` | Page analytics (reach, engagement) |

### fte-instagram — Python (`src/mcp/instagram_server.py`)
| Tool | Description |
|------|-------------|
| `create_ig_post` | Publish image post |
| `create_ig_reel` | Publish video reel |
| `get_ig_media` | List recent media |
| `get_ig_comments` | Read comments on media |
| `reply_ig_comment` | Reply to a comment |
| `get_ig_insights` | Account analytics |

### fte-twitter — Python (`src/mcp/twitter_server.py`)
| Tool | Description |
|------|-------------|
| `post_tweet` | Post a tweet |
| `get_my_tweets` | List recent tweets |
| `reply_to_tweet` | Reply to a tweet |
| `like_tweet` | Like a tweet |

### fte-linkedin — Python (`src/mcp/linkedin_server.py`)
| Tool | Description |
|------|-------------|
| `create_linkedin_post` | Publish post to LinkedIn |
| `get_linkedin_posts` | List recent posts |
| `get_linkedin_profile` | Get profile information |
| `comment_on_linkedin_post` | Comment on a post |
| `like_linkedin_post` | Like a post |

---

## Agent Skills (17 Skills)

All AI functionality is defined as Agent Skills in `.claude/skills/`:

| Skill File | Purpose |
|------------|---------|
| `email_responder.md` | Process EMAIL_*.md files, trigger cross-domain workflows |
| `whatsapp_handler.md` | Process WA_*.md files, draft responses based on keywords |
| `plan_creator.md` | Generate PLAN_*.md reasoning scratchpads for complex tasks |
| `create_approval_request.md` | Create HITL approval files for sensitive actions |
| `process_document.md` | Process documents dropped into the vault |
| `update_dashboard.md` | Refresh Dashboard.md with current metrics |
| `odoo_accountant.md` | Create invoices, record payments, track expenses via Odoo |
| `facebook_poster.md` | Create Facebook Page posts with approval workflow |
| `instagram_manager.md` | Publish Instagram posts and reels |
| `twitter_poster.md` | Post tweets and replies |
| `linkedin_poster.md` | Create LinkedIn posts for business |
| `ceo_briefing.md` | Generate weekly CEO briefing combining all domains |
| `audit_logger.md` | Log all actions to JSON audit trail with workflow tracking |
| `error_handler.md` | Error recovery with retry logic and owner notifications |
| `vault_sync_manager.md` | Git sync between Cloud and Local agents (Platinum) |
| `cloud_orchestrator.md` | Cloud-side orchestration — draft-only zone (Platinum) |
| `local_orchestrator.md` | Local-side orchestration — full permissions (Platinum) |

---

## Security

### Credentials
- All secrets in `.env` file (never committed — in `.gitignore`)
- OAuth tokens in `.secrets/` directory (gitignored)
- Browser sessions in `.sessions/` directory (gitignored)
- No hardcoded API keys in codebase

### Human-in-the-Loop Approval

| Action | Policy | Reason |
|--------|--------|--------|
| Draft invoice | Auto-Approve | Drafts are safe, no external action |
| Invoice reply email | Auto-Approve | Confirmation emails are standard |
| Payment recording | **Require Approval** | Financial action needs human review |
| External email reply | **Require Approval** | Client communication needs review |
| Social media post | **Require Approval** | Public content needs review |
| Archive / no-action | Auto-Approve | No external action taken |

### Audit Logging
- Every action → `AI_Employee_Vault/Logs/YYYY-MM-DD.json`
- 90-day retention with automatic cleanup (runs daily at 03:00)
- Tracked fields: `timestamp`, `action_type`, `actor`, `target_file`, `status`, `workflow_id`, `domain`, `mcp_server`

### Testing Mode
Set `DRY_RUN=true` in `.env` — all actions are logged but not executed.

---

## Tier Checklist

### Bronze Tier: Foundation ✅
- [x] Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- [x] Gmail Watcher (OAuth2) + Filesystem Watcher (watchdog)
- [x] Claude Code reads from and writes to the vault
- [x] Folder structure: `/Needs_Action/`, `/Done/`, `/Logs/`, `/Plans/`, `/Pending_Approval/`
- [x] All AI functionality implemented as Agent Skills (17 skills)

### Silver Tier: Functional Assistant ✅
- [x] All Bronze requirements
- [x] 3 Watchers: Gmail + WhatsApp (Playwright) + Filesystem
- [x] LinkedIn auto-posting via `fte-linkedin` MCP server
- [x] Claude reasoning loop generates `PLAN_*.md` files (`src/utils/plan_manager.py`)
- [x] MCP email server (`fte-email`) — send + draft emails
- [x] Human-in-the-loop approval workflow (`src/orchestrator/approval_handler.py`)
- [x] APScheduler — CEO Briefing every Sunday 22:00, Audit Retention daily 03:00
- [x] All AI functionality as Agent Skills

### Gold Tier: Autonomous Employee ✅
- [x] All Silver requirements
- [x] Cross-domain integration with UUID workflow tracking (`src/orchestrator/workflow_engine.py`)
- [x] Odoo Community (Docker) + JSON-RPC MCP server — 6 tools (`src/mcp/odoo_server.py`)
- [x] Facebook integration — 5 MCP tools (`src/mcp/facebook_server.py`)
- [x] Instagram integration — 6 MCP tools including reels (`src/mcp/instagram_server.py`)
- [x] Twitter/X integration — 4 MCP tools via Playwright (`src/mcp/twitter_server.py`)
- [x] LinkedIn integration — 5 MCP tools (`src/mcp/linkedin_server.py`)
- [x] 6 MCP servers, 28 total tools (configured in `.mcp.json`)
- [x] Weekly CEO Briefing with PDF export + email delivery (`src/utils/ceo_briefing.py`)
- [x] Error recovery with exponential backoff (`src/utils/retry.py`)
- [x] Comprehensive audit logging with 90-day retention (`src/utils/logger.py`)
- [x] Ralph Wiggum loop — stop hook for autonomous task completion (`scripts/ralph-wiggum-check.sh`)
- [x] Architecture documentation (`docs/architecture.md` + `docs/lessons-learned.md`)
- [x] All AI functionality as Agent Skills

### Platinum Tier: Always-On Cloud + Local 🔄
Code is written and tested locally. Deployment requires a Cloud VM:

| Component | Code | Deploy |
|-----------|------|--------|
| Cloud Orchestrator (`src/orchestrator/cloud_orchestrator.py`) | ✅ | 🔄 Needs VM |
| Local Orchestrator (`src/orchestrator/local_orchestrator.py`) | ✅ | ✅ Ready |
| Git Vault Sync (`src/sync/git_sync.py`) | ✅ | 🔄 Needs VM |
| Work-Zone Split (Cloud=draft, Local=execute) | ✅ | 🔄 Needs VM |
| Odoo on Cloud + HTTPS (`config/nginx-odoo.conf`) | ✅ | 🔄 Needs VM |
| Health Monitor (`src/health/health_monitor.py`) | ✅ | 🔄 Needs VM |
| Local Auto-Start (`scripts/start-local-hidden.vbs`) | ✅ | ✅ Ready |
| PM2 Config (`config/ecosystem.config.js`) | ✅ | 🔄 Needs VM |

**Platinum Demo** (minimum passing gate):
```
Email arrives (laptop OFF) → Cloud drafts reply → Git push →
Local laptop ON → Git pull → User approves → Send via MCP → Done
```

---

## Project Structure

```
full-time-equivalent-project/
│
├── AI_Employee_Vault/              # Obsidian vault
│   ├── Dashboard.md                # System status
│   ├── Company_Handbook.md         # Rules of engagement
│   ├── Needs_Action/               # Incoming tasks
│   ├── Plans/                      # PLAN_*.md reasoning files
│   ├── Pending_Approval/           # Awaiting human review
│   ├── Approved/                   # Ready to execute
│   ├── Rejected/                   # Rejected by human
│   ├── Done/                       # Completed tasks
│   ├── Tasks/                      # Task tracking
│   ├── Logs/                       # YYYY-MM-DD.json audit logs
│   └── Briefings/                  # CEO_Briefing_*.md reports
│
├── src/
│   ├── main.py                     # Entry point (12 commands)
│   ├── watchers/
│   │   ├── gmail_watcher.py        # Gmail polling (OAuth2)
│   │   ├── gmail_auth.py           # Gmail auth flow
│   │   ├── whatsapp_watcher.py     # WhatsApp (Playwright)
│   │   └── filesystem_watcher.py   # File drop detection (watchdog)
│   ├── orchestrator/
│   │   ├── orchestrator.py         # Main loop
│   │   ├── approval_handler.py     # HITL approval workflow
│   │   ├── workflow_engine.py      # Cross-domain tracking
│   │   ├── cloud_orchestrator.py   # Platinum: cloud-side
│   │   ├── local_orchestrator.py   # Platinum: local-side
│   │   ├── vault_manager.py        # Vault file operations
│   │   └── model_selector.py       # AI model selection
│   ├── mcp/
│   │   ├── index.js                # fte-email (Node.js)
│   │   ├── email_server.py         # fte-email (Python backup)
│   │   ├── odoo_server.py          # fte-odoo (6 tools)
│   │   ├── facebook_server.py      # fte-facebook (5 tools)
│   │   ├── instagram_server.py     # fte-instagram (6 tools)
│   │   ├── twitter_server.py       # fte-twitter (4 tools)
│   │   ├── linkedin_server.py      # fte-linkedin (5 tools)
│   │   └── _meta_client.py         # Shared Meta API client
│   ├── playwright/
│   │   ├── linkedin_bot.py         # LinkedIn automation
│   │   └── twitter_bot.py          # Twitter automation
│   ├── scheduler/
│   │   └── jobs.py                 # CEO Briefing (Sun 22:00), Audit (daily 03:00)
│   ├── dashboard/
│   │   └── app.py                  # Streamlit dashboard (7 sections)
│   ├── utils/
│   │   ├── ceo_briefing.py         # CEO briefing generator
│   │   ├── email_sender.py         # Gmail send (HTML + attachments)
│   │   ├── logger.py               # Audit logging
│   │   ├── audit_retention.py      # 90-day log cleanup
│   │   ├── plan_manager.py         # Plan file management
│   │   ├── retry.py                # Exponential backoff
│   │   └── whatsapp_sender.py      # WhatsApp message sending
│   ├── sync/
│   │   └── git_sync.py             # Vault git sync (Platinum)
│   └── health/
│       └── health_monitor.py       # Health checks (Platinum)
│
├── .claude/skills/                 # 17 Agent Skill definitions
├── config/
│   ├── docker-compose-odoo.yml     # Odoo 17 + PostgreSQL 15
│   ├── cloud-agent.yaml            # Cloud config (Platinum)
│   ├── local-agent.yaml            # Local config (Platinum)
│   ├── ecosystem.config.js         # PM2 process config
│   ├── nginx-odoo.conf             # Nginx reverse proxy
│   ├── schedules.json              # Scheduled tasks
│   └── keywords.json               # WhatsApp keyword triggers
├── scripts/
│   ├── ralph-wiggum-check.sh       # Stop hook (autonomous loop)
│   ├── setup-cloud-vm.sh           # Cloud VM setup (Platinum)
│   ├── start-cloud.sh              # Cloud startup (Platinum)
│   ├── start-local.sh              # Local startup (Platinum)
│   ├── start-local-hidden.vbs      # Windows auto-start
│   ├── health-monitor.sh           # Health checks
│   └── backup-odoo.sh              # Odoo DB backup
├── docs/
│   ├── architecture.md             # System architecture
│   └── lessons-learned.md          # Development insights
├── Learning/
│   ├── Gmail_API_Setup_Guide.md
│   ├── LinkedIn_API_Setup_Guide.md
│   └── Meta_API_Facebook_Instagram_Setup_Guide.md
├── specs/                          # Spec-Driven Development artifacts
│   ├── 002-silver-fte-foundation/
│   ├── 003-gold-fte-autonomous/
│   └── 004-platinum-cloud-local/
│
├── .mcp.json                       # MCP server configuration
├── .env.example                    # Environment variable template
├── pyproject.toml                  # Python project (requires >=3.12)
└── CLAUDE.md                       # Claude Code instructions
```

---

## Troubleshooting

### Gmail

| Error | Solution |
|-------|----------|
| "Token has been expired or revoked" | `rm .secrets/gmail_token.json` then `uv run python -m src.main gmail --authorize` |
| "Missing required parameter: redirect_uri" | Check Google Cloud Console → Credentials → redirect URI. See `Learning/Gmail_API_Setup_Guide.md` |
| "Gmail credentials path not set" | Add `GMAIL_CREDENTIALS_PATH=.secrets/gmail_credentials.json` to `.env` |

### Odoo

| Error | Solution |
|-------|----------|
| "Odoo Not Set Up" on dashboard | Run `docker-compose -f config/docker-compose-odoo.yml up -d`, wait 60s, refresh |
| "Auth failed" | Open `http://localhost:8069`, create database `fte-ai-employee`, verify `.env` credentials |
| Dashboard timeout on Finance | Odoo Docker may be starting — wait 60 seconds and refresh |

### MCP Servers

| Error | Solution |
|-------|----------|
| MCP server won't connect | Check `.mcp.json` exists with all 6 servers configured |
| Email MCP fails | Run `cd src/mcp && node index.js` to test standalone |
| Facebook/Instagram API error | Verify `FB_PAGE_ACCESS_TOKEN` and `IG_ACCESS_TOKEN` in `.env` are valid |

### Dashboard

| Error | Solution |
|-------|----------|
| Dashboard won't start | `uv run python -m src.main dashboard` or `uv run streamlit run src/dashboard/app.py --server.port 8501` |
| "Module not found" | Run `uv sync` to install dependencies |

### WhatsApp

| Error | Solution |
|-------|----------|
| "Session expired" | Delete `.sessions/whatsapp/` then `uv run python -m src.main whatsapp --setup` |
| QR code not appearing | Ensure Playwright Chromium is installed: `uv run playwright install chromium` |

---

## Demo Video

[Coming Soon]

---

## Credits

Built by **Agentive Solutions** for [Panaversity Hackathon 0: Personal AI Employee](https://panaversity.org)

| Component | Credit |
|-----------|--------|
| Reasoning Engine | Claude Code (Opus 4.6) by Anthropic |
| Web Dashboard | Streamlit |
| Accounting | Odoo 17 Community Edition |
| Social Media APIs | Meta Graph API, LinkedIn REST API |
| Browser Automation | Playwright |
| Development Methodology | Spec-Driven Development (SDD) via SpecKit Plus |

---

*All code is original or properly attributed open-source. Built for the Panaversity Hackathon 0.*
