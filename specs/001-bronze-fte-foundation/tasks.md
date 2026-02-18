# Tasks: Bronze Tier — Personal AI Employee Foundation

**Input**: Design documents from `/specs/001-bronze-fte-foundation/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Include tests as requested in spec.md Success Criteria (SC-001 to SC-007)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1=Vault Setup, US2=File Watcher, US3=Orchestrator, US4=Agent Skills

---

## Phase 1: Setup (Project Infrastructure)

**Purpose**: Initialize project structure and dependencies

- [ ] T001 Create project directory structure per plan.md (src/, tests/, .claude/skills/)
- [ ] T002 Initialize Python project with `uv init` and pyproject.toml
- [ ] T003 [P] Install dependencies: watchdog>=4.0.0, python-dotenv>=1.0
- [ ] T004 [P] Install dev dependencies: pytest>=8.0, pytest-asyncio>=0.23
- [ ] T005 [P] Create .env.example with VAULT_PATH, POLL_INTERVAL, CLAUDE_TIMEOUT, DRY_RUN
- [ ] T006 [P] Create .gitignore (exclude .env, __pycache__, .venv, Logs/*.json)
- [ ] T007 Create conftest.py with pytest fixtures for vault testing

**Checkpoint**: Project structure ready, dependencies installed

---

## Phase 2: User Story 1 — Vault Setup & File Organization (Priority: P1) 🎯 MVP

**Goal**: Create structured Obsidian vault with all required folders and config files

**Independent Test**: Vault exists with all subfolders, Dashboard.md and Company_Handbook.md open in Obsidian

### Tests for User Story 1

- [ ] T008 [P] [US1] Unit test for vault creation in tests/unit/test_vault_setup.py
- [ ] T009 [P] [US1] Unit test for Dashboard.md template in tests/unit/test_dashboard.py
- [ ] T010 [P] [US1] Unit test for Company_Handbook.md validation in tests/unit/test_handbook.py

### Implementation for User Story 1

- [ ] T011 [US1] Create vault initialization script in src/utils/vault_init.py
- [ ] T012 [US1] Implement folder structure creation: Inbox/, Needs_Action/, Done/, Logs/, Pending_Approval/, Approved/, Rejected/
- [ ] T013 [US1] Create Dashboard.md template with placeholders per data-model.md
- [ ] T014 [US1] Create Company_Handbook.md with Bronze tier rules (approval thresholds, forbidden actions)
- [ ] T015 [US1] Add validation to ensure vault path exists and is writable
- [ ] T016 [US1] Create setup CLI command: `python -m src.main setup`

**Checkpoint**: Vault folder exists with all subfolders. Dashboard.md and Company_Handbook.md display correctly in Obsidian.

---

## Phase 3: User Story 2 — File System Watcher (Priority: P2)

**Goal**: Detect new files in Inbox/ and create action files in Needs_Action/

**Independent Test**: Drop PDF in Inbox/ → FILE_*.md appears in Needs_Action/ within 60 seconds

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test for file detection in tests/unit/test_filesystem_watcher.py
- [ ] T018 [P] [US2] Unit test for action file creation in tests/unit/test_action_file.py
- [ ] T019 [P] [US2] Unit test for rejected file handling in tests/unit/test_rejected_files.py
- [ ] T020 [US2] Integration test for watcher + action file flow in tests/integration/test_watcher_flow.py

### Implementation for User Story 2

- [ ] T021 [US2] Create base watcher class in src/watchers/base_watcher.py
- [ ] T022 [US2] Implement filesystem watcher using watchdog in src/watchers/filesystem_watcher.py
- [ ] T023 [US2] Implement file type validation (reject .exe, .bat, .sh, .cmd)
- [ ] T024 [US2] Create action file generator with YAML frontmatter per action-file.schema.json
- [ ] T025 [US2] Implement FILE_<name>.md naming convention with sanitization
- [ ] T026 [US2] Implement REJECTED_<name>.md for unsupported file types
- [ ] T027 [US2] Add startup scan for missed files (when watcher was down)

**Checkpoint**: File dropped in Inbox/ creates action file in Needs_Action/ within 60 seconds. Executables are rejected.

---

## Phase 4: User Story 3 — Orchestrator Triggers Claude Code (Priority: P3)

**Goal**: Poll Needs_Action/, trigger Claude Code, move completed files to Done/

**Independent Test**: Place .md file in Needs_Action/ → Claude processes it → file moves to Done/ within 2 minutes

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for folder polling in tests/unit/test_orchestrator.py
- [ ] T029 [P] [US3] Unit test for Claude Code triggering in tests/unit/test_claude_trigger.py
- [ ] T030 [P] [US3] Unit test for file movement in tests/unit/test_file_movement.py
- [ ] T031 [US3] Integration test for orchestrator + Claude flow in tests/integration/test_orchestrator_flow.py

### Implementation for User Story 3

- [ ] T032 [US3] Create orchestrator class in src/orchestrator/orchestrator.py
- [ ] T033 [US3] Implement Needs_Action/ polling with configurable interval (default: 60s)
- [ ] T034 [US3] Implement Claude Code subprocess trigger with subprocess.run()
- [ ] T035 [US3] Add timeout handling (5 minutes) and retry logic (max 3 attempts)
- [ ] T036 [US3] Implement file movement: Needs_Action/ → Done/
- [ ] T037 [US3] Add "Claude busy" detection to avoid duplicate triggers
- [ ] T038 [US3] Implement chronological processing (oldest file first)

**Checkpoint**: Orchestrator detects file, triggers Claude, moves to Done/. Dashboard.md shows activity.

---

## Phase 5: User Story 4 — Agent Skills Govern AI Behavior (Priority: P4)

**Goal**: All AI behavior defined as named skills in .claude/skills/

**Independent Test**: .claude/skills/ contains 3+ skill files. Claude uses skills when processing.

### Tests for User Story 4

- [ ] T039 [P] [US4] Unit test for skill file validation in tests/unit/test_skills.py
- [ ] T040 [P] [US4] Unit test for skill invocation logging in tests/unit/test_skill_logging.py

### Implementation for User Story 4

- [ ] T041 [P] [US4] Create process_document.md skill in .claude/skills/
- [ ] T042 [P] [US4] Create update_dashboard.md skill in .claude/skills/
- [ ] T043 [P] [US4] Create create_approval_request.md skill in .claude/skills/
- [ ] T044 [US4] Validate skills follow required structure (Purpose, Inputs, Steps, Output, Logging, Error Handling)
- [ ] T045 [US4] Add skill invocation logging to Logs/YYYY-MM-DD.json

**Checkpoint**: All 3 skills exist. Claude reads and follows skill procedures.

---

## Phase 6: HITL Approval Workflow

**Goal**: Sensitive actions require human approval before execution

**Independent Test**: Payment action creates approval file. Moving to Approved/ continues processing.

### Tests for HITL

- [ ] T046 [P] Unit test for approval file creation in tests/unit/test_approval.py
- [ ] T047 [P] Unit test for approval/rejection handling in tests/unit/test_approval_flow.py
- [ ] T048 Integration test for full HITL flow in tests/integration/test_hitl_flow.py

### Implementation for HITL

- [ ] T049 Implement approval file creation per approval-file.schema.json
- [ ] T050 Add Pending_Approval/ watcher to detect owner decisions
- [ ] T051 Implement Approved/ detection → continue processing → move to Done/
- [ ] T052 Implement Rejected/ detection → log rejection → move original to Done/
- [ ] T053 Add first-move-wins logic for conflicting moves
- [ ] T054 Update Dashboard.md to show "⚠️ Action Pending Approval" when files exist in Pending_Approval/

**Checkpoint**: Sensitive actions halt until approved. Approval/rejection logged correctly.

---

## Phase 7: Audit Logging

**Goal**: Every AI action produces a log entry in Logs/YYYY-MM-DD.json

**Independent Test**: Process a file → check Logs/ → entry exists with correct fields

### Tests for Logging

- [ ] T055 [P] Unit test for log entry creation in tests/unit/test_logger.py
- [ ] T056 [P] Unit test for log file rotation (daily) in tests/unit/test_log_rotation.py

### Implementation for Logging

- [ ] T057 Create logger utility in src/utils/logger.py
- [ ] T058 Implement JSON log file per day: Logs/YYYY-MM-DD.json
- [ ] T059 Implement log entry format per log-entry.schema.json
- [ ] T060 Add logging calls to: watcher (file_detected), orchestrator (processing_started), Claude (processing_completed)
- [ ] T061 Implement log entry validation (required fields, UUID generation)

**Checkpoint**: All actions logged. Log file is valid JSON array.

---

## Phase 8: Dashboard Updates

**Goal**: Dashboard.md reflects real-time vault status

**Independent Test**: Process file → Dashboard shows updated counts and Recent Activity

### Implementation for Dashboard

- [ ] T062 Implement Dashboard update function in src/utils/dashboard.py
- [ ] T063 Update pending count from Needs_Action/ file count
- [ ] T064 Update approval count from Pending_Approval/ file count
- [ ] T065 Update completed today from Done/ files with today's date
- [ ] T066 Update Recent Activity from last 5 log entries
- [ ] T067 Update Status: Idle/Working/Waiting for Approval based on state
- [ ] T068 Trigger Dashboard update after every state change

**Checkpoint**: Dashboard.md shows accurate real-time information.

---

## Phase 9: Process Management & Main Entry Point

**Goal**: Watcher and orchestrator run continuously, auto-restart on crash

**Independent Test**: Kill process → PM2 restarts within 60 seconds

### Implementation for Process Management

- [ ] T069 Create main.py entry point that starts watcher + orchestrator
- [ ] T070 Implement graceful shutdown handling (SIGTERM, SIGINT)
- [ ] T071 Create PM2 ecosystem.config.js for process management
- [ ] T072 Add PM2 startup script for reboot survival
- [ ] T073 [P] Create run.sh convenience script for development

**Checkpoint**: `pm2 start` runs system. Kill process → auto-restart.

---

## Phase 10: Polish & Validation

**Purpose**: Final validation against Success Criteria

- [ ] T074 Validate SC-001: File detection within 60 seconds (10 consecutive tests)
- [ ] T075 Validate SC-002: Processing completes within 2 minutes
- [ ] T076 Validate SC-003: Sensitive actions NEVER proceed without approval
- [ ] T077 Validate SC-004: 100% of actions have log entries
- [ ] T078 Validate SC-005: Crash recovery within 60 seconds
- [ ] T079 Validate SC-006: Dashboard shows 24-hour activity clearly
- [ ] T080 Validate SC-007: New skill requires only .md file creation
- [ ] T081 Run quickstart.md validation (full setup from scratch)
- [ ] T082 Update CLAUDE.md with Bronze tier completion status

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (Vault/US1) → Phase 3 (Watcher/US2)
                                    ↓
                              Phase 4 (Orchestrator/US3)
                                    ↓
                              Phase 5 (Skills/US4)
                                    ↓
                              Phase 6 (HITL)
                                    ↓
                              Phase 7 (Logging) ← Can start after Phase 2
                                    ↓
                              Phase 8 (Dashboard)
                                    ↓
                              Phase 9 (Process Mgmt)
                                    ↓
                              Phase 10 (Polish)
```

### User Story Dependencies

- **US1 (Vault Setup)**: No dependencies — can start immediately after Setup
- **US2 (File Watcher)**: Depends on US1 (needs vault folders to exist)
- **US3 (Orchestrator)**: Depends on US2 (needs action files to trigger)
- **US4 (Agent Skills)**: Depends on US1 (needs .claude/skills/ directory)

### Parallel Opportunities

Within each phase, tasks marked [P] can run in parallel:
- T003, T004, T005, T006 (Setup dependencies)
- T008, T009, T010 (US1 tests)
- T017, T018, T019 (US2 tests)
- T041, T042, T043 (Agent Skills creation)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1 (Vault)
3. **STOP and VALIDATE**: Open vault in Obsidian, verify structure
4. Manually test Dashboard.md and Company_Handbook.md

### Incremental Delivery

1. Setup + US1 → Vault ready
2. Add US2 → File detection working
3. Add US3 → Claude processing working
4. Add US4 → Skills governing behavior
5. Add HITL → Safety workflow complete
6. Add Logging + Dashboard → Full observability
7. Add Process Mgmt → Production ready

---

## Notes

- Tests marked [P] can run in parallel
- Each user story should be independently testable before moving on
- Commit after each task or logical group
- Run `pytest tests/` after each phase to catch regressions
- DRY_RUN=true in .env until fully tested
