<!--
SYNC IMPACT REPORT
==================
Version change: (template) → 1.0.0
New constitution — initial ratification.

Added sections:
- Core Principles (6 principles)
- Security Requirements
- Development Workflow
- Governance

Templates reviewed:
- .specify/templates/plan-template.md      ✅ aligned
- .specify/templates/spec-template.md      ✅ aligned
- .specify/templates/tasks-template.md     ✅ aligned

Deferred TODOs: none
-->

# Hackathon-0 Personal AI Employee Constitution

## Core Principles

### I. Local-First Architecture

All sensitive data (bank transactions, emails, WhatsApp sessions, credentials) MUST
reside on the local machine. External services may only receive non-sensitive,
processed outputs. The Obsidian vault is the single source of truth and MUST remain
local. Cloud sync (Platinum tier) MUST exclude secrets, tokens, and session files.

**Rationale**: Privacy is non-negotiable when an autonomous agent handles personal
and business affairs. Local-first ensures the user retains full ownership of their data.

### II. Human-in-the-Loop (HITL) Safety

The system MUST NOT execute sensitive actions autonomously. Every action in these
categories MUST create an approval file in `/Pending_Approval/` and wait:
- Payments of any amount to new recipients
- Payments above $100 to known recipients
- Emails to contacts not in the approved list
- Social media posts (replies and DMs)
- File deletions or moves outside the vault
- Any irreversible action

The system MUST only proceed after the approval file is moved to `/Approved/`.

**Rationale**: An autonomous agent acting on financial, communication, and business
data carries significant risk. HITL is the primary safety mechanism preventing
unintended consequences.

### III. Agent Skills First

Every AI functionality MUST be implemented as a named Agent Skill in
`.claude/skills/`. No business logic MUST be embedded in ad-hoc prompts.
Skills MUST be:
- Single-responsibility (one skill, one purpose)
- Self-contained with clear input/output contracts
- Documented with expected inputs, outputs, and side effects

**Rationale**: Agent Skills make AI behavior auditable, reusable, and maintainable.
They transform the system from prompt-dependent to architecture-driven.

### IV. Documentation-First Development

Before building any component, the developer MUST:
1. Research latest best practices and official documentation
2. Complete the full spec → plan → tasks → implement workflow
3. Verify the approach against the hackathon-0 documentation

No code MUST be written without an approved spec and plan.

**Rationale**: The hackathon's CLAUDE.md mandates "get full latest knowledge related
to that topic" before doing anything. This principle enforces that mandate structurally.

### V. Security by Design

Credentials, API keys, tokens, and passwords MUST NEVER appear in:
- Obsidian vault files (.md files)
- Git-committed files
- Agent Skill files
- Log files

All secrets MUST be stored in `.env` files (added to `.gitignore`) or the OS
keychain. Audit logs MUST be written for every action the AI takes.

**Rationale**: The system uses real credentials for Gmail, WhatsApp, and banking.
A single credential leak could cause severe personal and financial harm.

### VI. Tiered Complexity Growth

Features MUST be built incrementally following the hackathon tiers:
- **Bronze**: Foundation only — vault, one watcher, basic folder structure
- **Silver**: Add integrations — multiple watchers, one MCP server, scheduling
- **Gold**: Full autonomy — all integrations, Ralph Wiggum loop, CEO briefing
- **Platinum**: Cloud + local split — always-on, synced vault, delegation

No Silver/Gold features MUST be added to a Bronze implementation.
Each tier MUST be fully functional before advancing to the next.

**Rationale**: Incremental complexity prevents overengineering and ensures each tier
delivers a working, demonstrable AI Employee before adding more capabilities.

## Security Requirements

- `.env` files MUST be listed in `.gitignore` immediately upon creation
- Credentials MUST be rotated monthly and after any suspected breach
- All AI actions MUST be logged to `/Logs/YYYY-MM-DD.json` (90-day retention minimum)
- Watcher scripts MUST run in `DRY_RUN=true` mode during development
- Payment actions MUST NEVER be auto-retried — always require fresh human approval
- Rate limits MUST be enforced: max 10 emails/hour, max 3 payments/day (auto-approve)

### Sensitive Files — AI Agent Restrictions
AI agents (Claude Code, MCP tools, or any automated process) MUST NEVER:
- **Read or display** `.env`, `.secrets/*`, or any file containing credentials/tokens
- **Log, store, or expose** OAuth codes, access tokens, refresh tokens, or client secrets
- **Commit to git** any file in `.secrets/` directory
- **Display contents** of credential JSON files (e.g., `gmail_credentials.json`, `gmail_token.json`)

AI agents MAY only:
- Reference file **paths** and environment variable **names** (not values)
- Run scripts that **use** credentials internally without exposing them
- Tell the user which variables to add/update in `.env`

## Development Workflow

1. **Research**: Read official docs and hackathon documentation before any task
2. **Specify**: Run `/sp.specify` to create feature specification
3. **Plan**: Run `/sp.plan` to create implementation architecture
4. **Tasks**: Run `/sp.tasks` to generate ordered task list
5. **Implement**: Run `/sp.implement` to execute tasks
6. **Validate**: Test each watcher and skill independently before integration
7. **Commit**: Use `/sp.git.commit_pr` for all commits

All Python scripts MUST be managed via `uv` (project manager).
All Node.js packages MUST use npm with Node.js v24+.
Process management for watchers MUST use PM2 or supervisord.

## Governance

This constitution supersedes all other development practices for this project.
Amendments require:
1. A documented reason for the change
2. Version bump following semantic versioning (MAJOR.MINOR.PATCH)
3. Update to this file and propagation to affected templates

All pull requests MUST verify compliance with Principles I through VI before merge.
Complexity violations MUST be justified in the plan.md Complexity Tracking table.

This constitution is the authoritative reference. When in doubt, refer here first,
then to the hackathon documentation at:
https://docs.google.com/document/d/1ofTMR1IE7jEMvXM-rdsGXy6unI4DLS_gc6dmZo8WPkI

**Version**: 1.0.0 | **Ratified**: 2026-02-17 | **Last Amended**: 2026-02-17
