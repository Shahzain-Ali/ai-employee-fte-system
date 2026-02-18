---
id: "0001"
title: initial-project-constitution
stage: constitution
date: 2026-02-17
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: main
user: user
command: /sp.constitution
labels: ["constitution","hackathon-0","personal-ai-employee","setup"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - null
---

## Prompt

Run sp.constitution for Hackathon-0 Personal AI Employee project (Building Autonomous
FTEs in 2026). Establish project constitution with principles derived from hackathon
documentation and prior discussion covering Bronze/Silver/Gold/Platinum tiers.

## Response snapshot

Created constitution v1.0.0 with 6 core principles:
I. Local-First Architecture
II. Human-in-the-Loop (HITL) Safety
III. Agent Skills First
IV. Documentation-First Development
V. Security by Design
VI. Tiered Complexity Growth

Also defined Security Requirements, Development Workflow (uv + sp.* workflow), and
Governance sections. All templates reviewed and aligned.

## Outcome

- ✅ Impact: Project constitution established — all future work governed by 6 principles
- 🧪 Tests: N/A — constitution document, no tests
- 📁 Files: .specify/memory/constitution.md (created v1.0.0)
- 🔁 Next prompts: /sp.specify for Bronze tier feature specification
- 🧠 Reflection: Constitution derived from hackathon documentation + Bronze tier
  discussion. Captures HITL, local-first, and tiered growth as non-negotiable.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): none
- Next experiment: Run /sp.specify for Bronze tier
