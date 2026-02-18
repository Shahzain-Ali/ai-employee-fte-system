---
id: ed35a449-9c10-4d36-9655-6983c4e6fbf0
type: file_processing
status: pending
original_file: Inbox/invoice.txt
file_type: .txt
skill: process_document
created_at: 2026-02-18T09:20:19Z
---

# Action: Process invoice.txt

Process the file located at `Inbox/invoice.txt`.

Use the `process_document` skill as defined in `.claude/skills/process_document.md`.

## Steps

1. Read the file at `Inbox/invoice.txt`
2. Apply the `process_document` skill
3. Update this file's status to `completed`
4. Move this file to `Done/`
5. Update `Dashboard.md`
6. Write a log entry to `Logs/2026-02-18.json`
