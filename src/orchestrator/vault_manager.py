"""Vault Manager — file-based state management using folder-as-status pattern."""
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone

import yaml

logger = logging.getLogger(__name__)

# Valid vault folders (state transitions)
VAULT_FOLDERS = [
    "Needs_Action", "In_Progress", "Plans",
    "Pending_Approval", "Updates", "Done", "Logs", "Briefings",
]

# Valid domains
DOMAINS = ["email", "social", "invoice", "general"]


def create_task_file(
    vault_path: Path,
    domain: str,
    task_type: str,
    created_by: str,
    priority: str = "medium",
    body: str = "",
) -> Path:
    """Create a new task file in Needs_Action/<domain>/.

    Args:
        vault_path: Root path to the vault directory.
        domain: Task domain (email, social, invoice, general).
        task_type: Type of task (email_reply, social_post, etc.).
        created_by: Agent that created the task (cloud, local).
        priority: Priority level (low, medium, high, urgent).
        body: Markdown body content for the task.

    Returns:
        Path to the created task file.
    """
    vault = Path(vault_path)
    folder = vault / "Needs_Action" / domain
    folder.mkdir(parents=True, exist_ok=True)

    task_id = str(uuid.uuid4())[:12]
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    iso_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    filename = f"{domain}_{task_type}_{task_id}_{ts}.md"
    filepath = folder / filename

    frontmatter = {
        "id": task_id,
        "type": task_type,
        "domain": domain,
        "created_by": created_by,
        "created_at": iso_now,
        "claimed_by": None,
        "claimed_at": None,
        "status": "needs_action",
        "priority": priority,
    }

    content = "---\n" + yaml.dump(frontmatter, default_flow_style=False) + "---\n\n" + body
    filepath.write_text(content, encoding="utf-8")

    logger.info("Created task file: %s", filepath.relative_to(vault))
    return filepath


def move_task(vault_path: Path, task_file: Path, target_folder: str, subfolder: str = "") -> Path:
    """Move a task file to a different vault folder (state transition).

    Args:
        vault_path: Root path to the vault directory.
        task_file: Path to the task file to move.
        target_folder: Target folder name (e.g., 'In_Progress', 'Done').
        subfolder: Optional subfolder (e.g., 'cloud', 'email').

    Returns:
        New path of the moved file.
    """
    vault = Path(vault_path)

    if subfolder:
        target = vault / target_folder / subfolder
    else:
        target = vault / target_folder
    target.mkdir(parents=True, exist_ok=True)

    new_path = target / task_file.name

    # Handle name collision
    if new_path.exists():
        short_id = str(uuid.uuid4())[:8]
        new_path = target / f"{task_file.stem}_{short_id}.md"

    task_file.rename(new_path)
    logger.info("Moved task: %s → %s", task_file.name, new_path.relative_to(vault))

    # Update frontmatter status
    _update_frontmatter_field(new_path, "status", target_folder.lower().replace(" ", "_"))

    return new_path


def claim_task(vault_path: Path, task_file: Path, agent: str) -> Path:
    """Claim a task using the claim-by-move pattern.

    Moves from Needs_Action/<domain>/ to In_Progress/<agent>/.
    Updates frontmatter with claimed_by and claimed_at.

    Args:
        vault_path: Root path to the vault directory.
        task_file: Path to the task file in Needs_Action/.
        agent: Agent claiming the task ('cloud' or 'local').

    Returns:
        New path in In_Progress/<agent>/.

    Raises:
        FileNotFoundError: If the task file no longer exists (claimed by other agent).
    """
    if not task_file.exists():
        raise FileNotFoundError(f"Task already claimed or moved: {task_file}")

    new_path = move_task(vault_path, task_file, "In_Progress", subfolder=agent)

    # Update claim fields
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _update_frontmatter_field(new_path, "claimed_by", agent)
    _update_frontmatter_field(new_path, "claimed_at", now)
    _update_frontmatter_field(new_path, "status", "in_progress")

    logger.info("Task claimed by %s: %s", agent, new_path.name)
    return new_path


def list_tasks_by_folder(vault_path: Path, folder: str, subfolder: str = "") -> list[Path]:
    """List all task files (.md) in a vault folder.

    Args:
        vault_path: Root path to the vault directory.
        folder: Folder name (e.g., 'Needs_Action', 'Pending_Approval').
        subfolder: Optional subfolder (e.g., 'email', 'cloud').

    Returns:
        List of Path objects sorted by modification time (oldest first).
    """
    vault = Path(vault_path)

    if subfolder:
        target = vault / folder / subfolder
    else:
        target = vault / folder

    if not target.exists():
        return []

    files = [f for f in target.iterdir() if f.is_file() and f.suffix == ".md"]
    files.sort(key=lambda f: f.stat().st_mtime)
    return files


def read_task_frontmatter(task_file: Path) -> dict:
    """Read and parse YAML frontmatter from a task file.

    Args:
        task_file: Path to the task markdown file.

    Returns:
        Dict of frontmatter fields, or empty dict on parse failure.
    """
    try:
        content = task_file.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return {}
        end = content.index("---", 3)
        frontmatter_text = content[3:end].strip()
        return yaml.safe_load(frontmatter_text) or {}
    except (OSError, ValueError, yaml.YAMLError) as e:
        logger.error("Failed to read frontmatter from %s: %s", task_file, e)
        return {}


def write_status_update(
    vault_path: Path,
    agent: str,
    actions: list[str],
    pending_approvals: list[str] | None = None,
    alerts: list[str] | None = None,
) -> Path:
    """Write a status update file to Updates/ folder.

    Args:
        vault_path: Root path to the vault directory.
        agent: Agent writing the update ('cloud' or 'local').
        actions: List of action descriptions since last update.
        pending_approvals: List of pending approval file names.
        alerts: List of alert messages.

    Returns:
        Path to the created status update file.
    """
    vault = Path(vault_path)
    updates_dir = vault / "Updates"
    updates_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    iso_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    filename = f"cloud_status_{ts}.md"
    filepath = updates_dir / filename

    frontmatter = {
        "agent": agent,
        "timestamp": iso_now,
        "type": "status_update",
    }

    actions_text = "\n".join(f"- {a}" for a in actions) if actions else "- No actions"
    approvals_text = "\n".join(f"- {a}" for a in (pending_approvals or [])) or "- None"
    alerts_text = "\n".join(f"- {a}" for a in (alerts or [])) or "- None"

    content = (
        "---\n" + yaml.dump(frontmatter, default_flow_style=False) + "---\n\n"
        "## Actions Since Last Update\n\n" + actions_text + "\n\n"
        "## Pending Approvals\n\n" + approvals_text + "\n\n"
        "## Alerts\n\n" + alerts_text + "\n"
    )

    filepath.write_text(content, encoding="utf-8")
    logger.info("Status update written: %s", filename)
    return filepath


def _update_frontmatter_field(file_path: Path, field: str, value) -> None:
    """Update a single field in a task file's YAML frontmatter.

    Args:
        file_path: Path to the markdown file.
        field: Field name to update.
        value: New value for the field.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return

        end_idx = content.index("---", 3)
        frontmatter_text = content[3:end_idx]
        body = content[end_idx + 3:]

        frontmatter = yaml.safe_load(frontmatter_text) or {}
        frontmatter[field] = value

        new_content = "---\n" + yaml.dump(frontmatter, default_flow_style=False) + "---" + body
        file_path.write_text(new_content, encoding="utf-8")
    except (OSError, ValueError, yaml.YAMLError) as e:
        logger.error("Failed to update frontmatter field %s in %s: %s", field, file_path, e)
