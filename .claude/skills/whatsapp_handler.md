# Skill: WhatsApp Handler

## Purpose

Process incoming WhatsApp action files (WA_*.md) from Needs_Action/. Analyze the message content, determine appropriate action, and draft a response if needed.

## Platform

whatsapp

## Trigger

WA_*.md file detected in Needs_Action/

## Inputs

- **action_file**: Path to WA_*.md file in Needs_Action/
- **Company_Handbook.md**: Rules for message handling and approval requirements

## Steps

1. Read the WA_*.md action file frontmatter and body
2. Read Company_Handbook.md for message handling rules
3. Analyze the message:
   - Determine sender category (known contact vs unknown)
   - Assess urgency based on keywords matched
   - Identify required action (reply, forward, archive)
4. If **reply needed**:
   - Draft a brief, professional reply (1-3 sentences)
   - Create approval request in Pending_Approval/ using `src/utils/approval.py`
5. If **no action needed**:
   - Mark as processed
6. Write a summary note to Done/SUMMARY_{action_file_stem}.md
7. Update Dashboard.md with latest activity
8. Write log entry to Logs/YYYY-MM-DD.json

## Approval File Creation

When a reply requires approval, create the approval file:

```python
from src.utils.approval import create_approval_file

create_approval_file(
    vault_path=Path("AI_Employee_Vault"),
    action_type="other_sensitive",
    source_action_file="Needs_Action/WA_sender_timestamp.md",
    reason="WhatsApp reply to: sender_name — keyword message",
    details={
        "to": "sender_name",
        "message": "Draft reply text here",
        "reply_to": "Original message text",
        "platform": "whatsapp",
    },
)
```

## Approval Required

- Replies to unknown contacts: **ALWAYS requires approval**
- Replies mentioning money/payments: **ALWAYS requires approval**
- Replies to known contacts with non-sensitive content: No approval needed
- Archive/no-action: No approval needed

## Output

- Summary note in Done/
- If reply needed: Approval file in Pending_Approval/
- Log entry with: sender, message summary, action taken, approval status

## Logging

Log entry must include:
- action_type: "whatsapp_processed"
- source: "whatsapp_handler"
- platform: "whatsapp"
- details: sender, keywords_matched, action_taken (reply/archive)

## Error Handling

- Message body empty: Note "Empty message" and mark as processed
- Sender cannot be determined: Use "Unknown" as sender
- Media referenced but not available: Note in summary, continue processing
