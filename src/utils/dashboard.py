"""Dashboard updater — refreshes Dashboard.md with current vault stats."""
import logging
from pathlib import Path
from datetime import datetime, timezone
from src.utils.logger import AuditLogger

logger = logging.getLogger(__name__)


def update_dashboard(vault_path: Path) -> None:
    """Rewrite Dashboard.md with current vault statistics.

    Reads Needs_Action/, Pending_Approval/, Done/, and today's log file
    to produce an accurate real-time view of the AI Employee's status.

    Args:
        vault_path: Root path of the Obsidian vault.
    """
    vault_path = Path(vault_path)

    pending_count = _count_pending(vault_path)
    approval_count = _count_approvals(vault_path)
    completed_today = _count_completed_today(vault_path)
    status = _get_status(pending_count, approval_count)
    recent_activity = _get_recent_activity(vault_path)
    pending_approvals = _get_pending_approvals(vault_path)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content = f"""# AI Employee Dashboard

**Last Updated**: {now}
**Status**: {status}

## Current Stats

| Metric | Value |
|--------|-------|
| Pending Tasks | {pending_count} |
| Awaiting Approval | {approval_count} |
| Completed Today | {completed_today} |

## Recent Activity

{recent_activity}

## Pending Approvals

{pending_approvals}
"""
    dashboard_path = vault_path / "Dashboard.md"
    try:
        dashboard_path.write_text(content, encoding="utf-8")
        logger.debug("Dashboard.md updated")
    except OSError as e:
        logger.error("Failed to update Dashboard.md: %s", e)


def _count_pending(vault_path: Path) -> int:
    """Count FILE_*.md files in Needs_Action/."""
    needs_action = vault_path / "Needs_Action"
    if not needs_action.exists():
        return 0
    return sum(
        1 for f in needs_action.iterdir()
        if f.is_file() and f.name.startswith("FILE_") and f.suffix == ".md"
    )


def _count_approvals(vault_path: Path) -> int:
    """Count files in Pending_Approval/."""
    pending = vault_path / "Pending_Approval"
    if not pending.exists():
        return 0
    return sum(1 for f in pending.iterdir() if f.is_file())


def _count_completed_today(vault_path: Path) -> int:
    """Count files in Done/ that were modified today."""
    done = vault_path / "Done"
    if not done.exists():
        return 0
    today = datetime.now(timezone.utc).date()
    count = 0
    for f in done.iterdir():
        if f.is_file():
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).date()
            if mtime == today:
                count += 1
    return count


def _get_status(pending_count: int, approval_count: int) -> str:
    """Determine the current system status string."""
    if approval_count > 0:
        return "⚠️ Waiting for Approval"
    if pending_count > 0:
        return "🔄 Working"
    return "✅ Idle"


def _get_recent_activity(vault_path: Path) -> str:
    """Format the last 5 log entries as markdown bullet points."""
    audit = AuditLogger(vault_path=vault_path)
    entries = audit.get_recent(count=5)

    if not entries:
        return "_No activity recorded today._"

    lines = []
    for entry in entries:
        ts = entry.get("timestamp", "")[:16].replace("T", " ")
        action = entry.get("action_type", "unknown").replace("_", " ")
        source = entry.get("source", "")
        status = entry.get("status", "")
        target = entry.get("target_file", "")
        target_part = f" — `{target}`" if target else ""
        lines.append(f"- `{ts}` **{action}** ({source}) [{status}]{target_part}")

    return "\n".join(lines)


def _get_pending_approvals(vault_path: Path) -> str:
    """List all files in Pending_Approval/ as markdown links."""
    pending = vault_path / "Pending_Approval"
    if not pending.exists():
        return "_No approvals pending._"

    files = [f for f in pending.iterdir() if f.is_file() and f.name.startswith("APPROVAL_")]
    if not files:
        return "_No approvals pending._"

    lines = [f"- [[Pending_Approval/{f.name}]]" for f in sorted(files)]
    return "\n".join(lines)
