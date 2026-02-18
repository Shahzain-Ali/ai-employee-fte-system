# Skill: update_dashboard

## Purpose

Refresh Dashboard.md with current vault statistics, recent activity, and pending approvals.
This skill is called after every processing action to keep Dashboard.md accurate.

## Inputs

None — this skill reads vault state directly.

## Steps

1. Count files in `Needs_Action/` that start with `FILE_` → `pending_count`
2. Count files in `Pending_Approval/` → `approval_count`
3. Count files in `Done/` whose `created_at` or modification time is today → `completed_today`
4. Determine system status:
   - `"⚠️ Waiting for Approval"` if `approval_count > 0`
   - `"🔄 Working"` if `pending_count > 0`
   - `"✅ Idle"` otherwise
5. Read the last 5 entries from `Logs/YYYY-MM-DD.json` (today's log file).
   If file doesn't exist, recent_activity = "No activity recorded today."
6. List all files in `Pending_Approval/` as markdown links
7. Rewrite `Dashboard.md` with this exact structure:

```markdown
# AI Employee Dashboard

**Last Updated**: {ISO timestamp}
**Status**: {status}

## Current Stats

| Metric | Value |
|--------|-------|
| Pending Tasks | {pending_count} |
| Awaiting Approval | {approval_count} |
| Completed Today | {completed_today} |

## Recent Activity

{last 5 log entries as bullet points, newest first}

## Pending Approvals

{list of Pending_Approval/ files as [[WikiLinks]], or "_No approvals pending._"}
```

## Output

- Overwritten `Dashboard.md` with fresh data
- Log entry written:
  ```json
  {"action_type": "dashboard_updated", "source": "claude_code", "status": "success"}
  ```

## Error Handling

1. **Log file missing**: Show "No activity recorded today." in Recent Activity
2. **Count errors**: Show "Error reading count" and log the issue
3. **Write permission error**: Log the error and skip Dashboard update (do not crash)

## Logging

Write a single log entry after updating Dashboard. The `skill_used` field MUST be
`"update_dashboard"`.
