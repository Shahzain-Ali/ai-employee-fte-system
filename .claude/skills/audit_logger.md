# Skill: Audit Logger

## Purpose
Structured logging of every AI action with workflow tracking, duration measurement, and data sanitization.

## Platform
general

## Inputs
- Action details: action_type, source, status, target_file, details
- Optional: workflow_id, mcp_server, domain, duration_ms

## Steps

1. **Capture action details**:
   - timestamp (UTC ISO-8601)
   - action_type (e.g., odoo_invoice_created, fb_post_created)
   - source (which component triggered)
   - status (success/failure)
   - target_file (relative vault path)
   - duration_ms (execution time)
   - mcp_server (which MCP server, if applicable)
   - workflow_id (cross-domain link, if applicable)
   - domain (odoo/facebook/instagram/gmail/whatsapp)

2. **Sanitize sensitive data** — NEVER log:
   - Access tokens or API keys
   - Passwords or credentials
   - Credit card numbers
   - Full email addresses in details (use first 3 chars + ***)

3. **Write to structured JSON log**:
   - File: `Logs/YYYY-MM-DD.json`
   - Format: JSON array, one entry appended per action
   - Each entry has unique UUID

4. **Check retention policy**:
   - Log files older than 90 days should be cleaned up
   - The audit_retention job handles this automatically

## Output Format
JSON entry appended to `Logs/YYYY-MM-DD.json` with all fields from LogEntry dataclass.

## Error Handling
- If log write fails: Log to Python stderr, do not block the main action
- If disk is full: Create NOTIFICATION_disk_full.md in Needs_Action/
