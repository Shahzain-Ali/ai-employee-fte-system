"""Vault initialization — create folder structure and core vault files."""
from pathlib import Path
from datetime import datetime, timezone


VAULT_FOLDERS = [
    "Inbox",
    "Needs_Action",
    "Done",
    "Logs",
    "Pending_Approval",
    "Approved",
    "Rejected",
]


def create_vault(vault_path: Path) -> Path:
    """Create the vault directory and all required subfolders.

    Args:
        vault_path: Absolute path where the vault will be created.

    Returns:
        The vault path.

    Raises:
        PermissionError: If the path is not writable.
        OSError: If directory creation fails.
    """
    vault_path = Path(vault_path)
    vault_path.mkdir(parents=True, exist_ok=True)

    for folder in VAULT_FOLDERS:
        (vault_path / folder).mkdir(exist_ok=True)

    return vault_path


def create_vault_files(vault_path: Path) -> None:
    """Create Dashboard.md and Company_Handbook.md in the vault.

    Args:
        vault_path: Path to the initialized vault.
    """
    vault_path = Path(vault_path)
    _write_dashboard(vault_path)
    _write_handbook(vault_path)


def _write_dashboard(vault_path: Path) -> None:
    """Write the initial Dashboard.md file."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"""# AI Employee Dashboard

**Last Updated**: {now}
**Status**: Idle

## Current Stats

| Metric | Value |
|--------|-------|
| Pending Tasks | 0 |
| Awaiting Approval | 0 |
| Completed Today | 0 |

## Recent Activity

_No activity recorded yet._

## Pending Approvals

_No approvals pending._
"""
    (vault_path / "Dashboard.md").write_text(content, encoding="utf-8")


def _write_handbook(vault_path: Path) -> None:
    """Write the Company_Handbook.md file with Bronze tier rules."""
    content = """# Company Handbook — AI Employee Guidelines

## Identity

- **Role**: Personal Assistant (Bronze Tier)
- **Active Since**: 2026-02-17

## Working Hours

This AI Employee operates 24/7 when the watcher and orchestrator are running.

## Approval Requirements

The following actions ALWAYS require human approval before execution.
The system MUST create a file in `Pending_Approval/` and wait for it to be
moved to `Approved/` before proceeding:

1. **Payments** — Any payment of any amount to any recipient
2. **Emails** — Sending to any contact not in the approved list
3. **File Deletions** — Deleting any file from the vault or local machine
4. **Irreversible Actions** — Any action that cannot be undone

## Forbidden Actions

The AI Employee MUST NEVER:

- Access credentials, API keys, or tokens directly
- Execute .exe, .bat, .sh, .cmd, or other executable files
- Send any data outside the local machine without approval
- Modify this Handbook without explicit owner approval
- Skip the Pending_Approval/ workflow for any sensitive action
- Auto-retry a rejected payment action

## Escalation Rules

Immediately update Dashboard.md and alert the owner when:

- An error occurs 3 times in a row for the same file
- An unknown or unsupported file type is detected in Inbox/
- A file has been waiting in Needs_Action/ for more than 10 minutes
- More than 5 files are waiting in Pending_Approval/

## Approved Contacts

_Empty — all email recipients require approval in Bronze tier._

## File Processing Rules

| File Type | Action |
|-----------|--------|
| .pdf | Summarize, categorize |
| .png, .jpg, .jpeg | Note dimensions, suggest tagging |
| .docx, .txt, .md | Summarize content |
| .exe, .bat, .sh, .cmd | REJECT immediately |
| Unknown | REJECT and log |

## Response Guidelines

- Be concise and professional
- Use markdown formatting in all outputs
- Always log actions to `Logs/YYYY-MM-DD.json`
- Update `Dashboard.md` after completing any task
- Reference the skill name used in all log entries
"""
    (vault_path / "Company_Handbook.md").write_text(content, encoding="utf-8")
