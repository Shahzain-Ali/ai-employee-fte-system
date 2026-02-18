# Research: Bronze Tier Technology Decisions

**Feature**: 001-bronze-fte-foundation
**Date**: 2026-02-17
**Status**: Complete

---

## 1. File System Watching

### Decision: Use `watchdog` library

**Rationale**:
- Cross-platform support (Windows/WSL/Linux/macOS)
- Event-driven architecture — no CPU-intensive polling needed
- Well-maintained with 10k+ GitHub stars
- Explicitly recommended in hackathon-0 documentation

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| `watchdog` | Event-driven, cross-platform, mature | Requires installation | ✅ Selected |
| `watchfiles` | Fast (Rust-based) | Less documentation | Overkill for simple use case |
| `os.scandir` polling | No dependencies | CPU-intensive, misses quick changes | Not real-time enough |
| `inotify` (Linux only) | Native, fast | Linux-only, won't work on Windows | Not cross-platform |

---

## 2. Python Project Management

### Decision: Use `uv`

**Rationale**:
- Explicitly required in constitution Development Workflow
- Fast dependency resolution (Rust-based)
- Single tool for venv + packages
- Modern Python workflow standard

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| `uv` | Fast, modern, single tool | Newer, less docs | ✅ Selected (constitution mandate) |
| `pip` + `venv` | Builtin, familiar | Slow, two tools | Not as streamlined |
| `poetry` | Full featured | Slower, complex | Overhead for simple project |
| `conda` | Great for data science | Heavy, different ecosystem | Wrong use case |

---

## 3. Claude Code Triggering

### Decision: Use `subprocess.run()`

**Rationale**:
- Claude Code is a CLI tool — subprocess is the natural choice
- Allows capturing stdout/stderr for logging
- Built-in timeout support via `timeout` parameter
- No external dependencies

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| `subprocess.run()` | Simple, builtin, timeout support | Blocking | ✅ Selected |
| `subprocess.Popen` | Non-blocking | More complex | Bronze doesn't need concurrency |
| API calls | Could be faster | Claude Code has no API | Not available |

---

## 4. Audit Logging Format

### Decision: Use JSON files (one per day)

**Rationale**:
- Easy to parse with Python `json` module
- Human-readable when formatted
- No database setup required (local-first)
- Can be queried with `jq` for ad-hoc analysis
- File per day prevents single huge file

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| JSON files | Simple, parseable, local | No query engine | ✅ Selected |
| SQLite | Full SQL queries | Overkill for single user | Unnecessary complexity |
| Plain text | Human readable | Hard to parse | Can't query structured data |
| CSV | Spreadsheet compatible | Multiline values problematic | JSON handles nested better |

---

## 5. Process Management

### Decision: Use PM2

**Rationale**:
- Auto-restart on crash
- Log management built-in
- Startup scripts (survives reboot)
- Explicitly recommended in hackathon documentation
- Cross-platform via Node.js

**Alternatives Considered**:

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| PM2 | Full-featured, cross-platform | Requires Node.js | ✅ Selected (hackathon recommends) |
| `supervisord` | Python native | Config more complex | Less documented for this use |
| `systemd` | Linux native | Linux-only, complex | Not cross-platform |
| `nohup` | Simple | No auto-restart | No crash recovery |

---

## 6. Configuration Management

### Decision: Use `.env` files with `python-dotenv`

**Rationale**:
- Standard pattern for secrets management
- Easy to exclude from git via `.gitignore`
- Constitution Principle V mandates no credentials in vault
- `python-dotenv` is lightweight and mature

**Configuration Values** (stored in `.env`):

```
VAULT_PATH=/path/to/AI_Employee_Vault
POLL_INTERVAL=60
CLAUDE_TIMEOUT=300
DRY_RUN=true
```

---

## 7. Action File Format

### Decision: YAML frontmatter in Markdown files

**Rationale**:
- Compatible with Obsidian's metadata system
- Human-readable in both editor and Obsidian
- Can be parsed with `pyyaml` or simple regex
- Matches hackathon documentation examples

**Example Format**:

```markdown
---
type: file_drop
original_name: invoice_january.pdf
file_size: 102400
detected_at: 2026-02-17T10:30:00Z
status: pending
priority: normal
---

## File Dropped for Processing

New file detected in Inbox/.

## Suggested Actions
- [ ] Analyze content
- [ ] Categorize document
- [ ] Update relevant records
```

---

## Research Complete

All technology decisions are finalized. No NEEDS CLARIFICATION items remain.
Proceed with `/sp.tasks` to generate implementation task list.
