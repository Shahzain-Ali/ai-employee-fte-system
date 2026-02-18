# Implementation Plan: Bronze Tier — Personal AI Employee Foundation

**Branch**: `001-bronze-fte-foundation` | **Date**: 2026-02-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bronze-fte-foundation/spec.md`

---

## Summary

Build the foundational layer of a Personal AI Employee system: a local Obsidian vault
with organized folder structure, a File System Watcher that detects dropped files,
an Orchestrator that triggers Claude Code for processing, and Agent Skills that
define all AI behavior. The system follows HITL safety for sensitive actions and
maintains complete audit logs. This Bronze tier is the MVP that all future tiers
(Silver/Gold/Platinum) will build upon.

---

## Technical Context

**Language/Version**: Python 3.14.3 (WSL) — managed via `uv`
**Primary Dependencies**: watchdog (file system events), pathlib (file operations),
json (logging), subprocess (Claude Code triggering)
**Storage**: Local filesystem (Obsidian vault) — markdown files for data, JSON for logs
**Testing**: pytest with pytest-asyncio for async watcher tests
**Target Platform**: Windows 11 + WSL2 (Ubuntu 24.04) — scripts run in WSL
**Project Type**: Single project (CLI scripts + Obsidian vault)
**Performance Goals**: File detection within 60 seconds, Claude processing within 2 minutes
**Constraints**: Local-first (no cloud), single user, vault under 1GB
**Scale/Scope**: 1 user, ~100 files/day max, ~50 skills max

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Bronze Compliance | Status |
|-----------|-------------|-------------------|--------|
| I. Local-First | All data on local machine | Vault is local folder, no cloud sync | ✅ PASS |
| II. HITL Safety | Sensitive actions need approval | Pending_Approval/ + Approved/ workflow | ✅ PASS |
| III. Agent Skills | All AI logic in skills | .claude/skills/ directory planned | ✅ PASS |
| IV. Documentation-First | Spec → plan → tasks → implement | Following this workflow now | ✅ PASS |
| V. Security by Design | No credentials in vault | .env for secrets, .gitignore setup | ✅ PASS |
| VI. Tiered Growth | Bronze features only | No Gmail/WhatsApp/MCP (Silver), no Ralph loop (Gold) | ✅ PASS |

**Gate Status**: ✅ ALL PASSED — proceed with Phase 0

---

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-fte-foundation/
├── spec.md              # Feature requirements (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output - technology decisions
├── data-model.md        # Phase 1 output - entity definitions
├── quickstart.md        # Phase 1 output - setup instructions
├── contracts/           # Phase 1 output - file format schemas
│   ├── action-file.schema.json
│   ├── approval-file.schema.json
│   └── log-entry.schema.json
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
# Obsidian Vault (the AI Employee's workspace)
AI_Employee_Vault/
├── Dashboard.md              # Real-time status view
├── Company_Handbook.md       # Agent behavior rules
├── Inbox/                    # Manual file drop location
├── Needs_Action/             # Pending tasks (created by watchers)
├── Done/                     # Completed tasks
├── Logs/                     # JSON audit logs (YYYY-MM-DD.json)
├── Pending_Approval/         # Sensitive actions awaiting human decision
├── Approved/                 # Human-approved actions
└── Rejected/                 # Human-rejected actions

# Python Scripts (WSL execution)
src/
├── watchers/
│   ├── __init__.py
│   ├── base_watcher.py       # Abstract base class for all watchers
│   └── filesystem_watcher.py # Inbox/ folder monitor
├── orchestrator/
│   ├── __init__.py
│   └── orchestrator.py       # Polls Needs_Action/, triggers Claude
├── utils/
│   ├── __init__.py
│   ├── logger.py             # JSON audit logging
│   └── file_ops.py           # Vault file operations
└── main.py                   # Entry point — starts watcher + orchestrator

# Agent Skills (Claude Code reads these)
.claude/
└── skills/
    ├── process_document.md       # Generic document processing
    ├── update_dashboard.md       # Dashboard.md update procedure
    └── create_approval_request.md # HITL approval workflow

# Tests
tests/
├── unit/
│   ├── test_logger.py
│   └── test_file_ops.py
├── integration/
│   ├── test_filesystem_watcher.py
│   └── test_orchestrator.py
└── conftest.py               # pytest fixtures

# Configuration
pyproject.toml                # uv project config
.env.example                  # Template for secrets
.gitignore                    # Excludes .env, vault secrets, logs
```

**Structure Decision**: Single project with clear separation between vault (data),
scripts (automation), and skills (AI behavior). All Python managed via `uv`.

---

## Component Architecture

### 1. File System Watcher

```
┌─────────────────────────────────────────────────────────────────┐
│                     File System Watcher                         │
├─────────────────────────────────────────────────────────────────┤
│ Input:  Inbox/ folder (watchdog FileSystemEventHandler)         │
│ Output: Needs_Action/FILE_<name>.md                             │
│ Process:                                                        │
│   1. Watchdog detects on_created event                          │
│   2. Validate file type (reject .exe, .bat, etc.)               │
│   3. Extract metadata (name, size, type, timestamp)             │
│   4. Create action file with YAML frontmatter                   │
│   5. Log event to Logs/YYYY-MM-DD.json                          │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Orchestrator

```
┌─────────────────────────────────────────────────────────────────┐
│                        Orchestrator                             │
├─────────────────────────────────────────────────────────────────┤
│ Input:  Needs_Action/ folder (polling every 60 seconds)         │
│ Output: Claude Code subprocess, Dashboard.md update             │
│ Process:                                                        │
│   1. Poll Needs_Action/ for .md files with status: pending      │
│   2. If files exist and Claude not running, trigger Claude      │
│   3. Claude reads Company_Handbook.md + action file             │
│   4. Claude processes using appropriate Agent Skill             │
│   5. Claude moves file to Done/ or creates approval request     │
│   6. Orchestrator updates Dashboard.md Recent Activity          │
└─────────────────────────────────────────────────────────────────┘
```

### 3. HITL Approval Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   HITL Approval Workflow                        │
├─────────────────────────────────────────────────────────────────┤
│ Trigger: Claude detects sensitive action per Company_Handbook   │
│ Process:                                                        │
│   1. Claude creates approval file in Pending_Approval/          │
│   2. Dashboard.md shows "⚠️ Action Pending Approval"            │
│   3. Owner reviews file in Obsidian                             │
│   4. Owner moves file to Approved/ or Rejected/                 │
│   5. Orchestrator detects move → triggers Claude to continue    │
│   6. If Approved → execute action → move to Done/               │
│   7. If Rejected → log rejection → move original to Done/       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Decisions

### Why watchdog for File System Watching?

- Cross-platform (works on Windows/WSL/Linux/Mac)
- Event-driven (no polling needed for file detection)
- Mature library with good documentation
- Recommended in hackathon documentation

### Why subprocess for Claude Code Triggering?

- Claude Code is a CLI tool — subprocess.run() is natural
- Allows capturing stdout/stderr for logging
- Simple, reliable, no external dependencies
- Timeout support built-in

### Why JSON for Audit Logs?

- Easy to parse programmatically
- Human-readable when formatted
- Supports structured queries
- No database setup required (aligns with local-first)

### Why PM2 for Process Management?

- Auto-restart on crash
- Log management
- Startup scripts (survives reboot)
- Cross-platform (Node.js-based)
- Recommended in hackathon documentation

---

## Complexity Tracking

> No violations — Bronze tier is intentionally simple per Constitution Principle VI.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | —          | —                                   |

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Watcher misses files | Low | Medium | watchdog is reliable; add startup scan for missed files |
| Claude Code times out | Medium | Low | 5-minute timeout; retry once; log failure |
| Approval file moved to both folders | Low | Medium | First-move-wins logic; warn on conflict |
| Vault corruption | Low | High | Git version control; daily backup recommendation |

---

## Dependencies

### Python Packages (via uv)

```toml
[project]
dependencies = [
    "watchdog>=4.0.0",    # File system events
    "python-dotenv>=1.0", # .env loading
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]
```

### External Tools

- **Claude Code**: v2.1.42+ (installed)
- **PM2**: For process management (install via npm)
- **Obsidian**: v1.10.6+ (installed)

---

## Next Steps

1. `/sp.tasks` — Generate ordered task list from this plan
2. `/sp.implement` — Execute tasks to build Bronze tier
3. Test each component independently
4. Integration test: drop file → watcher → orchestrator → Claude → Done
5. Document in quickstart.md how to run the system
