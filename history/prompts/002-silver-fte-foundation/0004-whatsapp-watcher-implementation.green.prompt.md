---
id: 0004
title: WhatsApp Watcher Implementation
stage: green
date: 2026-02-22
surface: agent
model: claude-opus-4-6
feature: 002-silver-fte-foundation
branch: 002-silver-fte-foundation
user: agentive-solution
command: implement
labels: ["whatsapp", "playwright", "watcher", "silver-tier"]
links:
  spec: specs/002-silver-fte-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - src/watchers/whatsapp_watcher.py
  - src/main.py
  - config/keywords.json
  - .claude/skills/whatsapp_handler.md
  - pyproject.toml
  - .env
tests:
  - "Manual: whatsapp --setup (QR scan, session persisted)"
  - "Manual: whatsapp --once (badge detection, keyword match, action file creation)"
---

## Prompt

Okay so now we move to the whatsapp implementation but make sure the gmail working is not disturbed. Don't make any plan file just follow the specs of silver tier and documentation instructions etc.

## Response snapshot

Implemented WhatsApp Watcher using Playwright with persistent browser context for WhatsApp Web automation. Key implementation details:

1. **Badge-based approach**: Scans ALL visible chat rows in WhatsApp Web, finds ones with `span[aria-label*="unread"]` badge, processes max 5 unread chats.
2. **Playwright + stealth**: Uses `playwright-stealth` (`apply_stealth_sync`) for bot detection evasion, `launch_persistent_context` for session persistence across runs.
3. **DOM selectors discovered through debugging**:
   - Chat rows: `[aria-label="Chat list"] [role="row"]`
   - Unread badge: `span[aria-label*="unread"]`
   - Incoming messages: `div.message-in`
   - Message text: `div.copyable-text`
4. **Critical timing fix**: Added `time.sleep(5)` after chat list loads — badges need ~5 seconds to fully render on WhatsApp Web before they disappear when auto-read.
5. **State dedup**: `.state/whatsapp_processed.json` prevents re-processing same messages.
6. **Action files**: Creates `WA_{sender}_{timestamp}.md` in `Needs_Action/` with frontmatter metadata.

Test result: Successfully detected "urgent help needed for project" from Shahzain Ali Bangash, matched keywords `urgent` + `help`, created action file `WA_Shahzain_Ali_Bangash_20260222T100942Z.md`.

## Outcome

- ✅ Impact: WhatsApp Watcher fully functional — second watcher for Silver Tier requirement met
- 🧪 Tests: Manual end-to-end test passed (QR setup + message detection + action file creation)
- 📁 Files: 6 files created/modified
- 🔁 Next prompts: LinkedIn automation, MCP email server, scheduling
- 🧠 Reflection: WhatsApp Web DOM is fragile and undocumented; badge timing was the hardest debugging issue. The 5s wait is a pragmatic fix but may need tuning for slower connections.

## Evaluation notes (flywheel)

- Failure modes observed: Stealth API changed between v1/v2 (use→use_sync→apply_stealth_sync); DOM selectors differ from documented examples; badges disappear on auto-read requiring timing workaround
- Graders run and results (PASS/FAIL): Manual E2E PASS
- Prompt variant (if applicable): N/A
- Next experiment: Test with multiple unread chats simultaneously; test group message detection
