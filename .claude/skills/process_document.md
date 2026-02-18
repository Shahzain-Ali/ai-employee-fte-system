# Skill: process_document

## Purpose

Process a document dropped in Inbox/ that has been routed to Needs_Action/ via an action file.
Analyze the file, extract key information, and record findings.

## Inputs

Read the action file frontmatter for these values:
- `original_file`: path to the file inside the vault (e.g., `Inbox/invoice.pdf`)
- `file_type`: extension of the file (e.g., `.pdf`)
- `id`: UUID of this action task

## Steps

1. Read this action file to get `original_file` path
2. Read `Company_Handbook.md` to check processing rules for this file type
3. Analyze the original file based on its type:
   - `.pdf`: Extract title, page count, date, key topics
   - `.docx` / `.doc`: Summarize first 500 words, extract headings
   - `.txt` / `.md`: Summarize content in 3 bullets
   - `.csv`: Report column names and row count
   - `.png` / `.jpg` / `.jpeg`: Describe what is visible in the image
   - `.mp3` / `.mp4`: Note duration and format
   - Unknown: Describe filename and size only
4. Check if any sensitive action is required (payments, emails, deletions):
   - If YES: Use `create_approval_request` skill before proceeding
   - If NO: Continue to step 5
5. Write a brief summary of findings as a markdown note in `Done/`
6. Update this action file:
   - Change `status: pending` → `status: completed`
7. Move this action file to `Done/` (rename path)
8. Call `update_dashboard` skill to refresh Dashboard.md
9. Write a log entry using this format:
   ```json
   {
     "action_type": "processing_completed",
     "source": "claude_code",
     "target_file": "Done/<filename>",
     "skill_used": "process_document",
     "status": "success"
   }
   ```
10. Append the log entry to `Logs/YYYY-MM-DD.json` (today's date)

## Output

- Updated action file in `Done/` with `status: completed`
- Log entry appended to today's `Logs/YYYY-MM-DD.json`
- `Dashboard.md` updated with latest stats

## Error Handling

1. **File not found**: If `original_file` does not exist in Inbox/:
   - Update status to `failed`
   - Write error log entry
   - Move action file to `Done/` with failed status

2. **Unsupported file**: If file type is unknown:
   - Note filename and size only
   - Mark as completed with note "File type not recognized — logged for review"

3. **Sensitive action needed but approval pending**: Stop processing and wait.
   Do not mark as completed until approval is received.

## Logging

Every invocation MUST write to `Logs/YYYY-MM-DD.json`.
The `skill_used` field MUST be `"process_document"`.
