# Skill: Odoo Accountant

## Purpose
Manage Odoo accounting operations: create invoices, record payments, track expenses, and generate financial summaries via the fte-odoo MCP server.

## Platform
odoo

## Inputs
- Action file path (ODOO_*.md in Needs_Action/)
- Action type: `create_invoice`, `mark_paid`, `create_expense`, `get_summary`

## Steps

1. **Read the action file** at the provided path. Parse YAML frontmatter for:
   - `action`: The operation to perform
   - `partner_name`: Client name (for invoices)
   - `amount`: Amount (for invoices/expenses)
   - `due_date`: Due date (for invoices)
   - `workflow_id`: Cross-domain workflow link (if present)

2. **Determine the operation** based on `action` field:
   - `create_invoice` → Use `create_invoice` MCP tool
   - `mark_paid` → Use `mark_payment_received` MCP tool (REQUIRES APPROVAL)
   - `create_expense` → Use `create_expense` MCP tool
   - `get_summary` → Use `get_weekly_summary` MCP tool

3. **For payment actions (mark_paid)**: Create an approval request file in `Pending_Approval/`:
   - Filename: `APPROVAL_odoo_payment_{timestamp}.md`
   - Include invoice details, amount, and reason
   - Do NOT execute the payment until approved
   - Stop processing and wait for approval

4. **Invoke the appropriate MCP tool** with extracted parameters.

5. **Log the result** using the audit logger:
   - action_type: `odoo_invoice_created`, `odoo_payment_recorded`, or `odoo_expense_created`
   - mcp_server: `fte-odoo`
   - domain: `odoo`
   - Include workflow_id if present

6. **Update Dashboard.md** with latest financial data.

## Approval Rules
- **Payments**: ALL payment recording actions MUST be approved before execution
- **Invoices**: Can be created without approval (draft status)
- **Expenses**: Can be recorded without approval

## Output Format
Write a summary to `Done/SUMMARY_ODOO_{action}_{timestamp}.md` with:
- Action performed
- Result from Odoo (invoice ID, payment confirmation, etc.)
- Any errors encountered

## Error Handling
- If Odoo is unreachable: Log error, update component health to "down", create notification
- If authentication fails: Log error, create notification for owner
- If JSON-RPC error: Log the Odoo error message, keep action file for retry
- Never auto-retry payment operations
