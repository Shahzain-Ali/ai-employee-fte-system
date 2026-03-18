"""Audit log retention — archives/deletes log files older than configured days."""
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def cleanup_old_logs(vault_path: Path, retention_days: int = 90) -> dict:
    """Delete audit log files older than retention_days.

    Args:
        vault_path: Root path of the Obsidian vault.
        retention_days: Number of days to retain logs (default: 90).

    Returns:
        Dict with 'deleted_count', 'total_size_freed', 'errors'.
    """
    logs_dir = Path(vault_path) / "Logs"
    if not logs_dir.exists():
        return {"deleted_count": 0, "total_size_freed": 0, "errors": []}

    cutoff = datetime.now(timezone.utc).date() - timedelta(days=retention_days)
    deleted_count = 0
    total_freed = 0
    errors = []

    for log_file in logs_dir.glob("*.json"):
        # Parse date from filename: YYYY-MM-DD.json
        try:
            file_date = datetime.strptime(log_file.stem, "%Y-%m-%d").date()
        except ValueError:
            continue

        if file_date < cutoff:
            size = log_file.stat().st_size
            try:
                log_file.unlink()
                deleted_count += 1
                total_freed += size
                logger.info("Deleted old log: %s (%d bytes)", log_file.name, size)
            except OSError as e:
                errors.append(f"{log_file.name}: {e}")
                logger.error("Failed to delete %s: %s", log_file.name, e)

    return {
        "deleted_count": deleted_count,
        "total_size_freed": total_freed,
        "errors": errors,
    }


def get_log_disk_usage(vault_path: Path) -> dict:
    """Calculate total disk usage of audit logs.

    Args:
        vault_path: Root path of the Obsidian vault.

    Returns:
        Dict with 'total_bytes', 'file_count', 'oldest_date', 'newest_date'.
    """
    logs_dir = Path(vault_path) / "Logs"
    if not logs_dir.exists():
        return {"total_bytes": 0, "file_count": 0, "oldest_date": None, "newest_date": None}

    total = 0
    count = 0
    oldest = None
    newest = None

    for log_file in logs_dir.glob("*.json"):
        total += log_file.stat().st_size
        count += 1
        try:
            d = datetime.strptime(log_file.stem, "%Y-%m-%d").date()
            if oldest is None or d < oldest:
                oldest = d
            if newest is None or d > newest:
                newest = d
        except ValueError:
            pass

    return {
        "total_bytes": total,
        "file_count": count,
        "oldest_date": str(oldest) if oldest else None,
        "newest_date": str(newest) if newest else None,
    }
