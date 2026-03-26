# Skill: Email Responder

## Purpose

Process incoming email action files (EMAIL_*.md) from Needs_Action/. Analyze the email content, determine appropriate action, and execute cross-domain workflows when needed (e.g., invoice requests trigger Odoo integration).

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
   - **Detect cross-domain triggers** (see Cross-Domain Detection below)
4. If **invoice request detected** (Cross-Domain Flow — AUTO-APPROVED per Company Handbook):
   - Extract: client/partner name, line items (description + amount), due date
   - Use the `create_invoice` MCP tool (fte-odoo) to create the invoice in Odoo
   - Note the invoice ID and amount from the result
   - **Download invoice PDF**: Use the `get_invoice_pdf` MCP tool (fte-odoo) with the invoice ID
     - This returns a local file path to the PDF (e.g., `/tmp/fte_invoices/INV-2026-00001.pdf`)
   - Draft a brief professional reply email — DO NOT repeat line items or amounts in the body (the PDF has all details)
   - **Email body format** (industry standard — concise, professional):
     ```
     Dear {sender_name},

     Thank you for your request. Please find the attached invoice for your review.

     Invoice #: {invoice_name}
     Total Amount: PKR {total}
     Due Date: {due_date}

     Should you have any questions or require modifications, please do not hesitate to reach out.

     Best regards,
     Accounts Team
     ```
   - **Send reply with PDF attached**: Use the `send_email_tool` MCP tool (fte-email) with:
     - `to`: sender's email
     - `subject`: "Re: {original_subject} — Invoice #{invoice_name}"
     - `body`: the brief confirmation text above (NOT the full line items)
     - `attachment_path`: the PDF file path returned by `get_invoice_pdf`
   - This is auto-approved because: invoice is draft-only in Odoo (no money moves), and the reply is a factual confirmation
   - If `get_invoice_pdf` fails: still send reply WITHOUT attachment, but include line items in body as fallback
   - If Odoo MCP fails: still send reply noting "invoice pending", log the error
   - If email send fails: log error, write summary noting reply was not sent
   - **WhatsApp notification to Accounts Team**: After email is sent (or attempted), notify via WhatsApp:
     - Use the `send_whatsapp_message` MCP tool (fte-whatsapp) with:
       - `contact_name`: "Accounts Team"
       - `message`: "✅ Invoice Created\nClient: {partner_name}\nAmount: PKR {total}\nInvoice #: {invoice_name}\nEmail sent with PDF attached."
     - This is auto-approved (notification only, no sensitive action)
     - If WhatsApp send fails: log warning, do NOT block the workflow
5. If **regular reply needed** (no cross-domain):
   - Draft a professional reply (3-5 sentences max)
   - Check if sender is in approved contacts list
   - If sender unknown -> create approval request in Pending_Approval/ (REQUIRES APPROVAL)
   - If sender known and non-sensitive -> proceed
6. If **no action needed**:
   - Mark as processed
7. Write a summary to `Done/SUMMARY_{action_file_stem}.md` with all actions taken
8. Update Dashboard.md with latest activity
9. Write log entry to Logs/YYYY-MM-DD.json

## Cross-Domain Detection

Scan the email body for these patterns to trigger cross-domain workflows:

### Invoice Request Keywords
- "invoice", "bill", "billing", "payment request"
- "please invoice", "send invoice", "create invoice"
- "amount due", "total amount", "price quote"
- Currency symbols or amounts (PKR, USD, $, Rs.)

### Invoice Data Extraction
From the email body, extract:
- **partner_name**: The sender name or company from the `from` field
- **line_items**: Each service/product with description and price_unit
- **due_date**: Any mentioned due date (default: 30 days from today)

Example email body:
```
Please create an invoice for web development services.
- Website Design: PKR 50,000
- SEO Setup: PKR 25,000
Due by March 30, 2026
```

Extracted:
- partner_name: (from sender)
- lines: [{"description": "Website Design", "price_unit": 50000}, {"description": "SEO Setup", "price_unit": 25000}]
- due_date: "2026-03-30"

## Approval Rules (from Company Handbook)

### Auto-Approved (NO approval needed):
- **Invoice confirmation emails** — Client requests invoice, system creates it in Odoo, reply confirms it. Send directly.
- **Invoice creation in Odoo** — Draft invoices only, no money moves
- **Archive/no-action emails** — No reply needed, just process and move to Done/

### Requires Approval (MUST create Pending_Approval/ file):
- Replies to unknown/external contacts (non-invoice)
- Replies mentioning money amounts > $100 (non-invoice context)
- Any email that involves payment confirmation or money transfer
- Replies to known internal contacts: No approval needed

## Output

- If cross-domain (invoice): Invoice created in Odoo + reply email sent/drafted
- If reply needed with approval: Approval file in Pending_Approval/
- Completed action file moved to Done/
- Summary file in Done/SUMMARY_*.md
- Log entry with: sender, subject, action taken, cross-domain actions

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
- details: sender, subject, action_taken (reply/forward/archive/invoice_created)
- approval_status: required/not_required
- cross_domain: list of domains involved (e.g., ["odoo", "email"])
- workflow_id: unique ID linking all cross-domain actions (generate UUID if cross-domain)

## Error Handling

- Email body empty: Note "Empty email body" and mark as processed
- Sender cannot be parsed: Use raw "from" field as sender
- Attachment referenced but missing: Note in summary, continue processing
- Odoo unreachable: Log error, still draft the reply noting "invoice pending — Odoo temporarily unavailable"
- Email send fails: Log error, note in summary that reply was drafted but not sent
