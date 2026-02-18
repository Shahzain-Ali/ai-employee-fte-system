# Feature Specification: Hackathon-0 Bronze Tier — Personal AI Employee Foundation

**Feature Branch**: `001-bronze-fte-foundation`
**Created**: 2026-02-17
**Status**: Draft
**Input**: Hackathon-0 Bronze Tier: Personal AI Employee Foundation — Build a local-first
autonomous AI agent using Claude Code and Obsidian vault. Includes: proper vault folder
structure (Inbox, Needs_Action, Done, Logs, Pending_Approval, Approved, rejected), Dashboard.md,
Company_Handbook.md, one working File System Watcher Python script (using uv),
Orchestrator.py to trigger Claude Code, and all AI functionality implemented as Agent
Skills. Must follow HITL safety for sensitive actions and security-by-design principles.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Vault Setup & File Organization (Priority: P1)

A solo developer (the owner) sets up a structured local vault that serves as the
AI Employee's memory and workspace. The vault contains organized folders and two
core configuration files: a Dashboard showing current status and a Handbook
defining the AI's behavioral rules.

**Why this priority**: Without the vault structure, no other component can function.
This is the foundational layer all other features depend on.

**Independent Test**: Vault folder exists on disk with all required subfolders.
Dashboard.md and Company_Handbook.md open correctly in Obsidian and show proper
content. Claude Code can read and write files inside the vault.

**Acceptance Scenarios**:

1. **Given** no vault exists, **When** setup is complete, **Then** the vault folder
   contains Inbox/, Needs_Action/, Done/, Logs/, Pending_Approval/, Approved/, and
   Rejected/ subfolders, plus Dashboard.md and Company_Handbook.md files.

2. **Given** the vault exists, **When** the owner opens Obsidian and selects the
   vault folder, **Then** Dashboard.md displays current date, pending task count (0),
   and an empty Recent Activity section.

3. **Given** the vault exists, **When** Claude Code is launched from the vault
   directory, **Then** it successfully reads Company_Handbook.md rules and can
   write a test file to Needs_Action/.

---

### User Story 2 — File System Watcher Detects New Files (Priority: P2)

The owner drops any file (PDF, image, document) into the Inbox/ folder. A
background watcher script automatically detects the new file and creates a
corresponding action file in Needs_Action/ with metadata about the dropped file.

**Why this priority**: The watcher is the AI Employee's perception — without it,
the agent cannot detect new work autonomously.

**Independent Test**: Drop a test PDF into Inbox/. Within 60 seconds, a corresponding
.md file appears in Needs_Action/ with correct metadata (filename, size, timestamp).

**Acceptance Scenarios**:

1. **Given** the watcher is running, **When** a PDF file is dropped into Inbox/,
   **Then** within 60 seconds a file named FILE_<original_name>.md appears in
   Needs_Action/ containing the file type, original name, size, and timestamp.

2. **Given** the watcher is running, **When** multiple files are dropped at once,
   **Then** a separate .md file is created in Needs_Action/ for each dropped file.

3. **Given** the watcher crashes, **When** the process manager detects the crash,
   **Then** the watcher automatically restarts within 60 seconds.

---

### User Story 3 — Orchestrator Triggers Claude Code (Priority: P3)

When a new .md file appears in Needs_Action/, the Orchestrator script detects it
and triggers Claude Code to process the file according to the Company_Handbook rules.
Claude reads the file, reasons about the required action, and moves the file to
Done/ upon completion, updating Dashboard.md.

**Why this priority**: Orchestration connects perception to reasoning. Without it,
Claude must be manually triggered — removing autonomy.

**Independent Test**: Place a test .md file in Needs_Action/. Within 2 minutes,
Claude processes it, Dashboard.md is updated, and the file moves to Done/.

**Acceptance Scenarios**:

1. **Given** the orchestrator is running and a file exists in Needs_Action/, **When**
   the orchestrator polls the folder, **Then** it triggers Claude Code within 60
   seconds of file creation.

2. **Given** Claude Code is triggered, **When** it reads a Needs_Action/ file,
   **Then** it follows the rules in Company_Handbook.md to determine the action.

3. **Given** Claude completes processing, **When** the task requires no human
   approval, **Then** the file moves from Needs_Action/ to Done/ and Dashboard.md
   shows the completed action in Recent Activity.

4. **Given** Claude detects a sensitive action, **When** processing the file,
   **Then** it creates an approval file in Pending_Approval/ and halts processing
   until the owner moves that file to Approved/.

---

### User Story 4 — Agent Skills Govern All AI Behavior (Priority: P4)

All AI actions the agent performs are defined as named Agent Skills. The owner
can inspect, modify, and extend these skills without changing any code. Skills
cover document processing, dashboard updates, and approval workflows.

**Why this priority**: Skills make AI behavior transparent and maintainable —
a core principle of this project's constitution.

**Independent Test**: Open .claude/skills/ directory. At least 3 skill files exist.
Run Claude Code and verify it uses the skill procedures when processing files.

**Acceptance Scenarios**:

1. **Given** the vault is set up, **When** Claude Code starts, **Then** it reads
   all skill files from .claude/skills/ before processing any task.

2. **Given** a skill file exists for document processing, **When** a file arrives
   in Needs_Action/, **Then** Claude uses that skill's defined procedure.

3. **Given** a skill is invoked, **When** it completes, **Then** it produces a
   log entry in Logs/YYYY-MM-DD.json with timestamp, action type, and result.

---

### Edge Cases

- What happens when an unsupported file type (e.g., .exe) is dropped in Inbox/?
  Watcher creates a REJECTED_<filename>.md in Needs_Action/ with reason "unsupported type".
- What happens when Needs_Action/ has 20+ unprocessed files?
  Orchestrator processes them in chronological order, oldest first, one at a time.
- What happens when Claude Code is already running when orchestrator triggers it?
  Orchestrator waits 60 seconds and retries (max 3 attempts before logging failure).
- What happens when the owner moves an approval file to both Approved/ and Rejected/?
  First move wins; subsequent conflicting move is ignored and a warning is logged.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain a vault folder with these subfolders:
  Inbox/, Needs_Action/, Done/, Logs/, Pending_Approval/, Approved/, Rejected/.

- **FR-002**: Dashboard.md MUST display: current date, pending task count, recent
  activity (last 5 actions), and a status indicator (Idle / Working).

- **FR-003**: Company_Handbook.md MUST define: which actions require human approval,
  how to handle unknown file types, and the agent's response tone/behavior rules.

- **FR-004**: The File System Watcher MUST detect new files in Inbox/ within 60
  seconds and create corresponding .md action files in Needs_Action/.

- **FR-005**: Action files in Needs_Action/ MUST contain: file type, original
  filename, file size, detection timestamp, and initial status "pending".

- **FR-006**: The Orchestrator MUST poll Needs_Action/ at a configurable interval
  (default: 60 seconds) and trigger Claude Code when unprocessed files exist.

- **FR-007**: Claude Code MUST read Company_Handbook.md rules before processing
  any file in Needs_Action/.

- **FR-008**: For sensitive actions, the system MUST create an approval file in
  Pending_Approval/ and halt all processing of that task until the owner acts.

- **FR-009**: Upon task completion, the system MUST move the processed file from
  Needs_Action/ to Done/ and update Dashboard.md Recent Activity section.

- **FR-010**: Every AI action MUST produce a log entry in Logs/YYYY-MM-DD.json
  with: timestamp, action type, source file, result, and approval status.

- **FR-011**: All AI business logic MUST be implemented as named Agent Skills
  in .claude/skills/ — no ad-hoc prompts for repeatable tasks.

- **FR-012**: The watcher and orchestrator MUST auto-restart after crashes
  without requiring manual intervention from the owner.

### Key Entities

- **Vault**: Root folder serving as the AI Employee's entire memory and workspace.
  Contains all subfolders, configuration files, and action records.

- **Action File**: A markdown (.md) file in Needs_Action/ representing one pending
  unit of work. Created by watchers; consumed and moved by Claude Code.

- **Approval File**: A markdown file in Pending_Approval/ representing a sensitive
  pending action. Owner moves it to Approved/ to proceed or Rejected/ to cancel.

- **Agent Skill**: A markdown file in .claude/skills/ defining one reusable AI
  procedure. Has a clear name, purpose, inputs, steps, and expected output.

- **Dashboard**: The Dashboard.md file — owner's real-time status view showing
  pending count, recent activity, and current agent state.

- **Handbook**: The Company_Handbook.md file — the agent's rulebook defining
  behavior, approval thresholds, and response guidelines.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A file dropped in Inbox/ produces an action file in Needs_Action/
  within 60 seconds — verified across 10 consecutive test drops.

- **SC-002**: Claude Code processes an action file and updates Dashboard.md within
  2 minutes of the orchestrator triggering it — for standard (non-approval) tasks.

- **SC-003**: Sensitive actions NEVER proceed without an approval file being
  explicitly moved to Approved/ by the owner — zero exceptions allowed.

- **SC-004**: 100% of AI actions produce a corresponding log entry in
  Logs/YYYY-MM-DD.json — verified by comparing action count to log entry count.

- **SC-005**: The watcher and orchestrator resume operation automatically within
  60 seconds of a crash — verified by killing the process and observing restart.

- **SC-006**: The owner can understand what the AI Employee did in the last 24 hours
  by reading only Dashboard.md — no other file needs to be opened.

- **SC-007**: Adding a new Agent Skill requires only creating a new .md file in
  .claude/skills/ — zero code changes required.

---

## Assumptions

- The owner is the sole user — no multi-user access or permissions management needed.
- The vault resides on a Windows machine with WSL for Python script execution.
- Sensitive actions for Bronze tier are: payments, emails to unknown contacts, and
  file deletions — social media posting is out of scope (Silver tier).
- The watcher monitors only Inbox/ in Bronze tier — Gmail/WhatsApp are Silver tier.
- Vault size stays under 1GB during Bronze tier operation.
- The owner uses Obsidian to view the vault — no web UI or mobile app required.

---

## Out of Scope (Bronze Tier)

- Gmail, WhatsApp, or LinkedIn monitoring (Silver tier)
- MCP servers for sending emails or external actions (Silver tier)
- Ralph Wiggum autonomous loop (Gold tier)
- Monday CEO Briefing generation (Gold tier)
- Cloud deployment or vault sync (Platinum tier)
- Odoo accounting integration (Gold tier)
- Social media posting (Silver tier)
