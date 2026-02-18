---
id: "0001"
title: bronze-fte-foundation-spec
stage: spec
date: 2026-02-17
surface: agent
model: claude-opus-4-5-20251101
feature: 001-bronze-fte-foundation
branch: 001-bronze-fte-foundation
user: user
command: /sp.specify
labels: ["spec", "bronze-tier", "hackathon-0", "ai-employee", "foundation"]
links:
  spec: specs/001-bronze-fte-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-fte-foundation/spec.md
  - specs/001-bronze-fte-foundation/checklists/requirements.md
tests:
  - null
---

## Prompt

Hackathon-0 Bronze Tier: Personal AI Employee Foundation — Build a local-first
autonomous AI agent using Claude Code and Obsidian vault. Includes: proper vault folder
structure (Inbox, Needs_Action, Done, Logs, Pending_Approval, Approved), Dashboard.md,
Company_Handbook.md, one working File System Watcher Python script (using uv),
Orchestrator.py to trigger Claude Code, and all AI functionality implemented as Agent
Skills. Must follow HITL safety for sensitive actions and security-by-design principles.

## Response snapshot

Created comprehensive Bronze tier specification with:
- 4 User Stories (P1-P4): Vault Setup, File Watcher, Orchestrator, Agent Skills
- 12 Functional Requirements (FR-001 to FR-012)
- 6 Key Entities: Vault, Action File, Approval File, Agent Skill, Dashboard, Handbook
- 7 Success Criteria (SC-001 to SC-007) — all measurable and technology-agnostic
- Edge cases, assumptions, and clear Out of Scope section

## Outcome

- ✅ Impact: Complete Bronze tier spec ready for planning phase
- 🧪 Tests: N/A — specification document
- 📁 Files: spec.md created, requirements.md checklist passed all items
- 🔁 Next prompts: /sp.plan to create implementation architecture
- 🧠 Reflection: Spec follows hackathon documentation exactly. HITL safety for sensitive
  actions enforced. Clear Bronze vs Silver/Gold boundaries established.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): requirements.md checklist — all PASS
- Prompt variant (if applicable): none
- Next experiment: Proceed with /sp.plan
