"""Action file creation — converts Inbox files into Needs_Action task files."""
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone


# File types the AI Employee is allowed to process
ALLOWED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".txt", ".md", ".csv", ".json", ".xml",
    ".mp3", ".mp4", ".wav",
}

# Executable file types that are always rejected
REJECTED_EXTENSIONS = {
    ".exe", ".bat", ".sh", ".cmd", ".ps1", ".msi",
    ".dmg", ".pkg", ".deb", ".rpm", ".app",
}

# Skill to use based on file category
SKILL_MAP = {
    ".pdf": "process_document",
    ".docx": "process_document",
    ".doc": "process_document",
    ".txt": "process_document",
    ".md": "process_document",
    ".csv": "process_document",
    ".png": "process_document",
    ".jpg": "process_document",
    ".jpeg": "process_document",
    ".gif": "process_document",
    ".webp": "process_document",
    ".mp3": "process_document",
    ".mp4": "process_document",
    ".xlsx": "process_document",
    ".xls": "process_document",
}


def is_allowed_file_type(file_path: Path) -> bool:
    """Return True if the file extension is allowed for processing."""
    suffix = file_path.suffix.lower()
    return suffix in ALLOWED_EXTENSIONS


def sanitize_filename(name: str) -> str:
    """Replace spaces and special characters to make a safe filename."""
    name = name.replace(" ", "_")
    name = re.sub(r"[^\w.\-]", "", name)
    return name


def is_already_processed(source_file: Path, vault_path: Path) -> bool:
    """Check if this Inbox file was already handled in a previous run.

    Used during startup scan to skip files that were processed or rejected before.
    Industry standard: startup scan must be idempotent — never create duplicates.

    Checks for:
    - FILE_{name}.md in Needs_Action/ → currently being processed
    - FILE_{name}.md in Done/         → already completed
    - REJECTED_{name}.md in Needs_Action/ → already rejected

    Args:
        source_file: Path to the file in Inbox/.
        vault_path: Path to the vault root.

    Returns:
        True if this file was already handled and should be skipped.
    """
    vault_path = Path(vault_path)
    safe_name = sanitize_filename(source_file.name)

    # Already being processed
    if (vault_path / "Needs_Action" / f"FILE_{safe_name}.md").exists():
        return True

    # Already completed
    if (vault_path / "Done" / f"FILE_{safe_name}.md").exists():
        return True

    # Already rejected
    if (vault_path / "Needs_Action" / f"REJECTED_{safe_name}.md").exists():
        return True

    return False


def create_action_file(source_file: Path, vault_path: Path) -> Path:
    """Create a FILE_*.md action file in Needs_Action/ for an Inbox file.

    Args:
        source_file: Path to the file in Inbox/.
        vault_path: Path to the vault root.

    Returns:
        Path to the created action file.
    """
    vault_path = Path(vault_path)
    needs_action_dir = vault_path / "Needs_Action"

    safe_name = sanitize_filename(source_file.name)
    action_filename = f"FILE_{safe_name}.md"
    action_path = needs_action_dir / action_filename

    # If action file already exists in Needs_Action/, it is being processed — skip
    if action_path.exists():
        return action_path

    relative_source = source_file.relative_to(vault_path)
    suffix = source_file.suffix.lower()
    skill = SKILL_MAP.get(suffix, "process_document")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry_id = str(uuid.uuid4())

    content = f"""---
id: {entry_id}
type: file_processing
status: pending
original_file: {relative_source}
file_type: {suffix}
skill: {skill}
created_at: {now}
---

# Action: Process {source_file.name}

Process the file located at `{relative_source}`.

Use the `{skill}` skill as defined in `.claude/skills/{skill}.md`.

## Steps

1. Read the file at `{relative_source}`
2. Apply the `{skill}` skill
3. Update this file's status to `completed`
4. Move this file to `Done/`
5. Update `Dashboard.md`
6. Write a log entry to `Logs/{datetime.now(timezone.utc).strftime("%Y-%m-%d")}.json`
"""
    action_path.write_text(content, encoding="utf-8")
    return action_path


def create_rejected_file(source_file: Path, vault_path: Path, reason: str) -> Path:
    """Create a REJECTED_*.md file in Needs_Action/ for disallowed files.

    Args:
        source_file: Path to the rejected file in Inbox/.
        vault_path: Path to the vault root.
        reason: Human-readable reason for rejection.

    Returns:
        Path to the created rejection file.
    """
    vault_path = Path(vault_path)
    needs_action_dir = vault_path / "Needs_Action"

    safe_name = sanitize_filename(source_file.name)
    rejected_path = needs_action_dir / f"REJECTED_{safe_name}.md"

    relative_source = source_file.relative_to(vault_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry_id = str(uuid.uuid4())

    content = f"""---
id: {entry_id}
type: file_rejected
status: rejected
original_file: {relative_source}
reason: {reason}
created_at: {now}
---

# REJECTED: {source_file.name}

**Reason**: {reason}

The file `{source_file.name}` cannot be processed by the AI Employee.

## Action Required

- Review the file at `{relative_source}`
- Move or delete it manually
- This rejection file will be moved to `Done/` automatically

## Details

- **File**: {source_file.name}
- **Extension**: {source_file.suffix}
- **Detected at**: {now}
"""
    rejected_path.write_text(content, encoding="utf-8")
    return rejected_path
