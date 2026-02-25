# Skill: Email Responder

## Purpose

Process incoming email action files (EMAIL_*.md) from Needs_Action/. Analyze the email content, determine appropriate action, and draft a professional reply if needed.

## Platform

email

## Trigger

EMAIL_*.md file detected in Needs_Action/

## Inputs

- **action_file**: Path to EMAIL_*.md file in Needs_Action/
- **Company_Handbook.md**: Rules for email handling and approval requirements

## Steps

1. Read the EMAIL_*.md action file frontmatter and body
2. Read Company_Handbook.md for email handling rules
3. Analyze the email:
   - Determine sender category (known contact vs unknown)
   - Assess urgency (urgent keywords, sender importance)
   - Identify required action (reply, forward, archive)
4. If **reply needed**:
   - Draft a professional reply (3-5 sentences max)
   - Check if sender is in approved contacts list
   - If sender unknown → create approval request in Pending_Approval/
   - If sender known and non-sensitive → proceed
5. If **no action needed**:
   - Mark as processed
6. Update the action file status to `completed`
7. Move action file to Done/
8. Update Dashboard.md with latest activity
9. Write log entry to Logs/YYYY-MM-DD.json

## Approval Required

- Replies to unknown/external contacts: **ALWAYS requires approval**
- Replies mentioning money amounts > $100: **ALWAYS requires approval**
- Replies to known internal contacts: No approval needed
- Archive/no-action: No approval needed

## Output

- If reply needed with approval: Approval file in Pending_Approval/
- Completed action file moved to Done/
- Log entry with: sender, subject, action taken, approval status

## Approval File Creation

When a reply requires approval, create the approval file using `src/utils/approval.py`:

```python
from src.utils.approval import create_approval_file

create_approval_file(
    vault_path=Path("AI_Employee_Vault"),  # use actual vault path
    action_type="email_send",
    source_action_file="Needs_Action/EMAIL_xxxx.md",
    reason="Reply to external sender: sender@example.com",
    details={
        "to": "sender@example.com",
        "subject": "Re: Original Subject",
        "body": "Professional reply text - concise, clear, actionable",
    },
)
```

The approval file will be created in Pending_Approval/ with the format APPROVAL_email_send_TIMESTAMP.md.
The details dict MUST include `to`, `subject`, and `body` keys — these are used by the email sender after approval.

## Logging

Log entry must include:
- action_type: "email_processed"
- source: "email_responder"
- platform: "email"
- details: sender, subject, action_taken (reply/forward/archive)
- approval_status: required/not_required

## Error Handling

- Email body empty: Note "Empty email body" and mark as processed
- Sender cannot be parsed: Use raw "from" field as sender
- Attachment referenced but missing: Note in summary, continue processing
