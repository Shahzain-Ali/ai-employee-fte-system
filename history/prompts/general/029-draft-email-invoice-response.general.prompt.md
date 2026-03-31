---
id: 029
title: Draft Email Invoice Response
stage: general
date: 2026-03-31
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: architect
command: email_responder skill — draft reply
labels: ["email", "invoice", "draft", "cross-domain"]
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

Read the skill at /home/ubuntu/fte-project/.claude/skills/email_responder.md. Read the task at /home/ubuntu/fte-project/AI_Employee_Vault/In_Progress/cloud/EMAIL_19d1fe4b1d061e89.md. Create a DRAFT response — do NOT send. Write the draft under a Draft Reply section.

## Response snapshot

Analyzed incoming email from Shahzain Ali (shahzainalii859@gmail.com) requesting invoice for $5,000 for AI Automation Project (Tech Solutions Inc. / John Smith). Identified as cross-domain invoice request (AUTO-APPROVED per Company Handbook). Drafted professional reply with invoice details ($5,000, due 2026-04-30) and documented required cross-domain actions (Odoo invoice creation, PDF download, email send, WhatsApp notification). Draft written to EMAIL file — NOT sent per user instruction.

## Outcome

- ✅ Impact: Draft reply created in EMAIL action file with cross-domain action plan
- 🧪 Tests: N/A — draft only, no execution
- 📁 Files: EMAIL_19d1fe4b1d061e89.md updated with Draft Reply section
- 🔁 Next prompts: Execute cross-domain workflow (create Odoo invoice, send email with PDF, notify WhatsApp)
- 🧠 Reflection: User explicitly requested DRAFT only — respected constraint, documented all pending actions

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
