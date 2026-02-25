---
id: 002
title: Gold Tier Plan Creation
stage: plan
date: 2026-02-24
surface: agent
model: claude-opus-4-6
feature: 003-gold-fte-autonomous
branch: main
user: shahzain
command: /sp.plan
labels: ["gold-tier", "plan", "odoo", "facebook", "instagram", "mcp", "cross-domain", "ralph-wiggum"]
links:
  spec: specs/003-gold-fte-autonomous/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-gold-fte-autonomous/plan.md
  - specs/003-gold-fte-autonomous/research.md
  - specs/003-gold-fte-autonomous/data-model.md
  - specs/003-gold-fte-autonomous/quickstart.md
  - specs/003-gold-fte-autonomous/contracts/fte-odoo.md
  - specs/003-gold-fte-autonomous/contracts/fte-facebook.md
  - specs/003-gold-fte-autonomous/contracts/fte-instagram.md
  - CLAUDE.md
tests:
  - Constitution Check: 6/6 principles passed (pre-design)
  - Constitution Re-Check: 6/6 principles passed (post-design)
---

## Prompt

/sp.plan — Create architectural implementation plan for Gold Tier Autonomous Employee feature based on specs/003-gold-fte-autonomous/spec.md.

## Response snapshot

Created complete Gold Tier implementation plan with 7 artifacts:

1. **research.md** — Technology decisions for Odoo JSON-RPC, Meta Graph API, MCP server patterns, Ralph Wiggum hooks, audit logging, error recovery, CEO Briefing
2. **plan.md** — 6-phase implementation plan (A-F) with 23 steps, dependency graph, constitution checks, risk analysis
3. **data-model.md** — 9 entities: Odoo/FB/IG action files, CEO Briefing, extended audit logs, Ralph Wiggum tasks, component health, extended approvals/dashboard
4. **quickstart.md** — Step-by-step setup guide: Docker, Meta Developer Account, MCP registration, Ralph Wiggum hook, testing, security checklist
5. **contracts/fte-odoo.md** — 6 tools: create_invoice, get_invoices, mark_payment_received, get_weekly_summary, get_expenses, create_expense
6. **contracts/fte-facebook.md** — 5 tools: create_page_post, get_page_posts, get_post_comments, reply_to_comment, get_page_insights
7. **contracts/fte-instagram.md** — 6 tools: create_ig_post, create_ig_reel, get_ig_media, get_ig_comments, reply_ig_comment, get_ig_insights

Key architectural decisions: Python for all MCP servers, shared Meta Graph API client, dedicated workflow engine for cross-domain, Ralph Wiggum as bash Stop hook.

## Outcome

- ✅ Impact: Complete Gold Tier architectural plan ready for task generation
- 🧪 Tests: Constitution Check PASS (6/6 pre-design + 6/6 post-design)
- 📁 Files: 7 new files created, CLAUDE.md updated
- 🔁 Next prompts: /sp.tasks (task generation) → /sp.implement (implementation)
- 🧠 Reflection: 4 parallel research agents used for technology verification; all findings consolidated into research.md

## Evaluation notes (flywheel)

- Failure modes observed: Setup script detected wrong branch (002-silver); manually corrected Gold tier paths
- Graders run and results (PASS/FAIL): Constitution Check PASS, Post-Design Re-Check PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Proceed to /sp.tasks for task generation
