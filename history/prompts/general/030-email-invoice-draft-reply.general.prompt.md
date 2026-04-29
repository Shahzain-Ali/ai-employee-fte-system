---
id: 030
title: Email Invoice Draft Reply
stage: misc
date: 2026-03-31
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: human
command: general task
labels: ["email", "invoice", "draft-reply", "email-responder"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - AI_Employee_Vault/In_Progress/cloud/EMAIL_19d1fe4b1d061e89.md
tests:
  - none
---

## Prompt

Read the skill at /home/ubuntu/fte-project/.claude/skills/email_responder.md. Read the task at /home/ubuntu/fte-project/AI_Employee_Vault/In_Progress/cloud/EMAIL_19d1fe4b1d061e89.md. Create a DRAFT response — do NOT send, publish, or execute any final action. Write the draft content into the task file under a Draft Reply section. Do NOT call send_email_tool, create_page_post, create_ig_post, post_tweet, or any publish action.

## Response snapshot

Draft reply written to task file. Invoice request from Tech Solutions Inc ($5,000 for AI Automation Project). Professional reply drafted with cross-domain execution steps documented. No MCP tools called — draft only.

## Outcome

- Impact: Draft reply prepared for invoice request email from Shahzain Ali (shahzainalii859@gmail.com) at Tech Solutions Inc. No actions executed — safe draft-only workflow.
- Tests: Manual verification — no MCP tools invoked, draft written to correct task file section.
- Files: AI_Employee_Vault/In_Progress/cloud/EMAIL_19d1fe4b1d061e89.md (modified — Draft Reply section added)
- Next prompts: Review draft and approve send, or create invoice in Odoo and then send reply.
- Reflection: Draft-only pattern is safe for email workflows — allows human review before any irreversible action.

## Evaluation notes (flywheel)

- Failure modes observed: None — draft-only mode executed cleanly.
- Graders run and results (PASS/FAIL): PASS — no MCP tools called, draft content written correctly.
- Prompt variant (if applicable): email_responder skill + explicit draft-only constraint
- Next experiment: Test automated invoice creation + email send workflow with human approval gate.
