---
id: 0cbaf737-227b-45a3-9d75-d3a64a3ac310
type: file_processing
status: pending
original_file: Inbox/test.pdf
file_type: .pdf
skill: process_document
created_at: 2026-02-18T09:27:28Z
---

# Action: Process test.pdf

Process the file located at `Inbox/test.pdf`.

Use the `process_document` skill as defined in `.claude/skills/process_document.md`.

## Steps

1. Read the file at `Inbox/test.pdf`
2. Apply the `process_document` skill
3. Update this file's status to `completed`
4. Move this file to `Done/`
5. Update `Dashboard.md`
6. Write a log entry to `Logs/2026-02-18.json`
