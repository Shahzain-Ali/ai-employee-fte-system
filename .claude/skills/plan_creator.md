# Skill: Plan Creator

## Purpose

Create PLAN_{slug}_{date}.md reasoning scratchpads for complex multi-step tasks. Decompose a task into sequential steps, identify which steps require human approval, and manage step-by-step execution.

## Trigger

Complex task detected — any task requiring 2+ steps or involving external actions (email, WhatsApp, file creation).

## Inputs

- **task_description**: What needs to be done (from action file or direct request)
- **source_file**: Optional action file that triggered this (e.g., WA_*.md, EMAIL_*.md)
- **Company_Handbook.md**: Business rules and approval requirements

## When to Create a Plan

Create a Plan.md when the task involves ANY of:
- Multiple sequential actions (e.g., "check invoice and send email")
- External communication (email send, WhatsApp reply)
- Data lookup + action (e.g., "find client details and generate invoice")
- Cross-platform work (e.g., "read WhatsApp, reply via email")

Do NOT create a Plan.md for:
- Simple single-step actions (e.g., "archive this message")
- Information-only requests (e.g., "what was the last payment?")
- Direct replies with no follow-up

## Steps

1. Read the task description and source action file (if any)
2. Read Company_Handbook.md for business context and approval rules
3. Decompose the task into clear, sequential steps:
   - Each step should be a single atomic action
   - Order steps by dependency (what must happen first)
   - Mark steps that involve external actions as REQUIRES APPROVAL
4. Create the plan using PlanManager:

```python
from pathlib import Path
from src.utils.plan_manager import PlanManager

pm = PlanManager(vault_path=Path("AI_Employee_Vault"))

plan_path = pm.create_plan(
    task="Invoice Client A — 50,000 PKR",
    steps=[
        {"description": "Read Client A details from Company_Handbook.md", "requires_approval": False},
        {"description": "Generate invoice content", "requires_approval": False},
        {"description": "Create invoice file", "requires_approval": False},
        {"description": "Send invoice via email to Client A", "requires_approval": True},
        {"description": "Notify requester on WhatsApp", "requires_approval": True},
    ],
    source_file="Needs_Action/WA_Ayan_Jan_20260222.md",
)
```

5. Execute steps sequentially:

```python
# Get next step
next_step = pm.get_next_step(plan_path)

if next_step["requires_approval"]:
    # Create approval file in Pending_Approval/ and STOP
    # Wait for human to approve before continuing
    pass
else:
    # Execute the step
    # Then mark complete:
    pm.mark_step_complete(plan_path, next_step["number"], note="Result details here")
```

6. When a step REQUIRES APPROVAL:
   - Create the appropriate approval file (email, WhatsApp, etc.)
   - Update the plan step with "BLOCKED: awaiting approval"
   - STOP execution — do not proceed to next step
   - Resume after approval is granted

7. After all steps complete:
   - Write a summary to Done/SUMMARY_PLAN_{slug}.md
   - Update Dashboard.md
   - Write log entry

## Approval Rules

These actions ALWAYS require approval (mark with ⚠️ REQUIRES APPROVAL):
- Sending any email
- Sending any WhatsApp message
- Posting on LinkedIn
- Modifying or deleting files
- Any action involving money/payments
- Contacting external parties

These actions do NOT require approval:
- Reading files or data
- Internal calculations
- Creating draft content (not sending)
- Updating internal notes/logs

## Step Decomposition Guidelines

Good steps:
- "Read client details from Company_Handbook.md" (atomic, clear)
- "Generate invoice with line items" (single output)
- "Send email to client@example.com" (specific action)

Bad steps:
- "Handle the invoice situation" (too vague)
- "Read client details, calculate amount, and generate invoice" (too many actions)
- "Do everything" (not decomposed)

## Output

- PLAN_{slug}_{date}.md in Plans/ folder
- Each step has checkbox: `- [ ]` (pending) or `- [x]` (completed)
- Approval steps marked with ⚠️ REQUIRES APPROVAL
- Notes section updated as steps complete
- Summary in Done/ when plan completes

## Plan Status Lifecycle

```
in_progress → completed    (all steps done)
in_progress → blocked      (waiting for approval or external input)
blocked     → in_progress  (approval granted, resume execution)
```

## Error Handling

- Cannot determine steps: Ask for clarification, create plan with what's known
- Step fails: Add note to plan, mark step as failed, continue to next if independent
- Approval timeout (24h): Log reminder, keep plan in blocked state
