"""Dashboard updater — refreshes Dashboard.md with current vault stats."""
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from src.utils.logger import AuditLogger

logger = logging.getLogger(__name__)


def update_dashboard(vault_path: Path) -> None:
    """Rewrite Dashboard.md with current vault statistics.

    Reads Needs_Action/, Pending_Approval/, Done/, Logs/, and Plans/
    to produce an accurate real-time view of the AI Employee's status.

    Args:
        vault_path: Root path of the Obsidian vault.
    """
    vault_path = Path(vault_path)

    pending_count = _count_pending(vault_path)
    approval_count = _count_approvals(vault_path)
    completed_today = _count_completed_today(vault_path)
    status = _get_status(pending_count, approval_count)
    watcher_status = _get_watcher_status(vault_path)
    platform_stats = _get_platform_stats(vault_path)
    recent_activity = _get_recent_activity(vault_path)
    pending_approvals = _get_pending_approvals(vault_path)
    active_plans = _get_active_plans(vault_path)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    health_status = _get_health_status()
    financial_summary = _get_financial_summary(vault_path)

    content = f"""# AI Employee Dashboard

**Last Updated**: {now}
**Status**: {status}
**Tier**: Gold — Autonomous Employee

## Watcher Status

{watcher_status}

## System Health

{health_status}

## Current Stats

| Metric | Value |
|--------|-------|
| Pending Tasks | {pending_count} |
| Awaiting Approval | {approval_count} |
| Completed Today | {completed_today} |

## Financial Summary (Odoo)

{financial_summary}

## Platform Breakdown

{platform_stats}

## Active Plans

{active_plans}

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
    """Count actionable .md files in Needs_Action/ (FILE_*, EMAIL_*, WA_*)."""
    needs_action = vault_path / "Needs_Action"
    if not needs_action.exists():
        return 0
    prefixes = ("FILE_", "EMAIL_", "WA_", "ODOO_", "FB_", "IG_", "TW_", "LI_")
    return sum(
        1 for f in needs_action.iterdir()
        if f.is_file() and f.suffix == ".md" and any(f.name.startswith(p) for p in prefixes)
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


def _get_watcher_status(vault_path: Path) -> str:
    """Build a watcher status table from today's audit logs."""
    audit = AuditLogger(vault_path=vault_path)
    all_entries = audit.get_recent(count=200)

    watchers = {
        "Gmail": {"status": "Inactive", "last_check": "-", "items": 0, "source": "gmail_watcher"},
        "WhatsApp": {"status": "Inactive", "last_check": "-", "items": 0, "source": "whatsapp_watcher"},
        "Filesystem": {"status": "Inactive", "last_check": "-", "items": 0, "source": "filesystem_watcher"},
    }

    for entry in all_entries:
        source = entry.get("source", "")
        ts = entry.get("timestamp", "")
        for name, info in watchers.items():
            if source == info["source"]:
                info["status"] = "Active"
                if info["last_check"] == "-":
                    info["last_check"] = ts[:16].replace("T", " ")
                info["items"] += 1

    lines = [
        "| Watcher | Status | Last Activity | Items Today |",
        "|---------|--------|---------------|-------------|",
    ]
    for name, info in watchers.items():
        status_icon = "Active" if info["status"] == "Active" else "Inactive"
        lines.append(f"| {name} | {status_icon} | {info['last_check']} | {info['items']} |")

    return "\n".join(lines)


def _get_platform_stats(vault_path: Path) -> str:
    """Count completed items by platform (Email, WhatsApp, File)."""
    done = vault_path / "Done"
    if not done.exists():
        return "_No completed items._"

    today = datetime.now(timezone.utc).date()
    counts = {"Email": 0, "WhatsApp": 0, "File": 0, "Approval": 0,
              "Odoo": 0, "Facebook": 0, "Instagram": 0, "Twitter": 0, "LinkedIn": 0}

    for f in done.iterdir():
        if not f.is_file() or f.suffix != ".md":
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).date()
        if mtime != today:
            continue
        name = f.name
        if name.startswith("EMAIL_") or name.startswith("SUMMARY_EMAIL_"):
            counts["Email"] += 1
        elif name.startswith("WA_"):
            counts["WhatsApp"] += 1
        elif name.startswith("ODOO_") or name.startswith("SUMMARY_ODOO_"):
            counts["Odoo"] += 1
        elif name.startswith("FB_") or name.startswith("SUMMARY_FB_"):
            counts["Facebook"] += 1
        elif name.startswith("IG_") or name.startswith("SUMMARY_IG_"):
            counts["Instagram"] += 1
        elif name.startswith("TW_") or name.startswith("SUMMARY_TW_"):
            counts["Twitter"] += 1
        elif name.startswith("LI_") or name.startswith("SUMMARY_LI_"):
            counts["LinkedIn"] += 1
        elif name.startswith("APPROVAL_"):
            counts["Approval"] += 1
        elif name.startswith("FILE_") or name.startswith("SUMMARY_"):
            counts["File"] += 1

    if sum(counts.values()) == 0:
        return "_No completed items today._"

    lines = [
        "| Platform | Completed Today |",
        "|----------|-----------------|",
    ]
    for platform, count in counts.items():
        if count > 0:
            lines.append(f"| {platform} | {count} |")

    return "\n".join(lines)


def _get_health_status() -> str:
    """Build system health table from .state/health.json."""
    health_file = Path(".state/health.json")
    if not health_file.exists():
        return "_Health data not available._"

    try:
        data = json.loads(health_file.read_text(encoding="utf-8"))
        components = data.get("components", {})
    except (json.JSONDecodeError, OSError):
        return "_Health data not available._"

    status_icons = {"healthy": "Healthy", "degraded": "Degraded", "down": "DOWN", "unknown": "Unknown"}

    lines = [
        "| Component | Status | Last Check |",
        "|-----------|--------|------------|",
    ]
    for key, info in components.items():
        status = status_icons.get(info.get("status", "unknown"), "Unknown")
        last_check = info.get("last_check", "-")[:16].replace("T", " ")
        lines.append(f"| {info.get('name', key)} | {status} | {last_check} |")

    return "\n".join(lines)


def _get_financial_summary(vault_path: Path) -> str:
    """Get Odoo financial summary from latest CEO Briefing or cached data."""
    briefings_dir = vault_path / "Briefings"
    if not briefings_dir.exists():
        return "_No financial data available. Run CEO Briefing first._"

    # Find most recent briefing
    briefings = sorted(briefings_dir.glob("CEO_Briefing_*.md"), reverse=True)
    if not briefings:
        return "_No financial data available. Run CEO Briefing first._"

    try:
        content = briefings[0].read_text(encoding="utf-8")
        # Extract Financial Summary section
        if "## Financial Summary" in content:
            start = content.index("## Financial Summary")
            end = content.index("##", start + 3) if "##" in content[start + 3:] else len(content)
            return content[start:start + (end - start) if end > start else len(content)].strip()
    except (OSError, ValueError):
        pass

    return "_No financial data available._"


def _get_active_plans(vault_path: Path) -> str:
    """List active (in-progress) plans from Plans/ directory."""
    plans_dir = vault_path / "Plans"
    if not plans_dir.exists():
        return "_No active plans._"

    active = []
    for f in sorted(plans_dir.iterdir()):
        if not f.is_file() or not f.name.startswith("PLAN_"):
            continue
        content = f.read_text(encoding="utf-8")
        # Check if plan is still in progress (has unchecked items)
        total = content.count("- [")
        done = content.count("- [x]")
        if total > 0 and done < total:
            pct = int((done / total) * 100)
            active.append(f"- [[Plans/{f.name}]] — {done}/{total} steps ({pct}%)")

    if not active:
        return "_No active plans._"

    return "\n".join(active)
