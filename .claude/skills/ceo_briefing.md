# Skill: CEO Briefing

## Purpose
Generate a weekly business intelligence report combining financial, social media, and communication data from all integrated domains.

## Platform
general

## Inputs
- `week_start` (optional): Start date YYYY-MM-DD. Defaults to last Monday.

## Steps

1. **Collect data from all domains**:
   - **Odoo**: Revenue, pending invoices, expenses via direct JSON-RPC
   - **Facebook**: Post count and engagement from vault Done/ files
   - **Instagram**: Post count and engagement from vault Done/ files
   - **Gmail**: Email count from vault Done/ EMAIL_* files for the week
   - **WhatsApp**: Message count from vault Done/ WA_* files for the week

2. **Handle missing data sources gracefully**:
   - If a domain is unavailable, note it in `missing_sources`
   - Never silently omit — always document what's missing
   - Include available data regardless of missing sources

3. **Generate markdown report** following the CEO Briefing template from data-model.md:
   - YAML frontmatter with week dates, data sources, missing sources
   - Financial Summary table (Odoo)
   - Social Media table (Facebook + Instagram)
   - Communications summary (Gmail + WhatsApp)
   - Action Items section
   - Notes about missing sources

4. **Save to vault** at `Briefings/CEO_Briefing_YYYY-MM-DD.md`

5. **Optionally email to owner** via fte-email MCP `send_email_tool`:
   - Only if `OWNER_EMAIL` is configured in .env
   - Subject: "CEO Briefing — Week of {date}"
   - Body: The generated markdown (without YAML frontmatter)
   - Skip silently if OWNER_EMAIL not set

6. **Log the generation** in audit logs with action_type `ceo_briefing_generated`

## Output Format
Markdown report saved to `Briefings/CEO_Briefing_{end_date}.md` per data-model.md template.

## Error Handling
- If all domains fail: Still generate report with "all sources unavailable" note
- If Odoo is down: Skip financial section, note in missing_sources
- If email delivery fails: Log warning, do not block briefing generation
