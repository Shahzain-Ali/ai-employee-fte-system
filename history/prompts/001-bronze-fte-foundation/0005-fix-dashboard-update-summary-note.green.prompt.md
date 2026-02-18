---
id: "0005"
title: Fix Dashboard Update and Summary Note on DRY_RUN=false
stage: green
date: 2026-02-18
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-bronze-fte-foundation
branch: 001-bronze-fte-foundation
user: agentive-solution
command: implement plan
labels: ["bugfix","orchestrator","dashboard","summary-note"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/orchestrator/orchestrator.py
tests:
  - tests/unit/test_orchestrator.py
  - tests/unit/test_dashboard.py
  - tests/unit/test_claude_trigger.py
---

## Prompt

Implement the following plan:

# Fix: Dashboard Not Updating + No Summary Note (DRY_RUN=false)

## Root Cause Analysis

### Bug 1 — Dashboard not updated after real Claude run
`orchestrator.py` line 130–134: after `result.returncode == 0`, it calls `_move_to_done()`
but **never calls `update_dashboard()`**. That call only exists in the `dry_run` path (line 104).

### Bug 2 — No summary note in Done/
The prompt sent to Claude (line 108–113) says "follow the skill instructions exactly"
but **does NOT tell Claude where the skill file is**.
Claude has to guess — and it moves on without writing the summary.

Also: prompt says "move it to Done/" but orchestrator already does that — confusing duplication.

---

## Fixes

### Fix 1 — `src/orchestrator/orchestrator.py` (lines 130–140)

Add `update_dashboard()` and audit log in the success path.

### Fix 2 — `src/orchestrator/orchestrator.py` (lines 108–113)

Point Claude to the exact skill file and remove conflicting "move to Done/" instruction.

## Response snapshot

Applied both fixes to `src/orchestrator/orchestrator.py`:

**Fix 1**: Added `update_dashboard(self.vault_path)`, audit log (`processing_completed`), and `logger.info("Dashboard.md updated")` to the `result.returncode == 0` success branch.

**Fix 2**: Replaced the vague prompt with one that resolves the skill file path via `Path(__file__).parent.parent.parent / ".claude" / "skills" / "process_document.md"`, explicitly instructs Claude to write `Done/SUMMARY_{stem}.md`, and removes the conflicting "move to Done/" instruction.

All 55 tests passed.

## Outcome

- ✅ Impact: Dashboard now updates after real (non-dry-run) Claude executions; summary notes are written to Done/
- 🧪 Tests: 55/55 passed — uv run pytest
- 📁 Files: src/orchestrator/orchestrator.py (2 changes in _trigger_claude)
- 🔁 Next prompts: Drop a test file into Inbox/ with DRY_RUN=false to verify end-to-end
- 🧠 Reflection: Both bugs were in the same method; the dry_run branch was the reference — the real path was simply missing the same post-processing steps.

## Evaluation notes (flywheel)

- Failure modes observed: none — changes were minimal and targeted
- Graders run and results (PASS/FAIL): pytest 55/55 PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): add an integration test that mocks subprocess.run and asserts update_dashboard is called on returncode==0
