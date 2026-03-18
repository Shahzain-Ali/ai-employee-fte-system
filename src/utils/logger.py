"""Audit logger — writes every AI action to Logs/YYYY-MM-DD.json."""
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

_py_logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """A single audit log entry."""
    action_type: str
    source: str
    status: str
    target_file: Optional[str] = None
    details: dict = field(default_factory=dict)
    approval_status: str = "not_required"
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    # Gold tier fields
    workflow_id: Optional[str] = None
    mcp_server: Optional[str] = None
    retry_count: Optional[int] = None
    error_message: Optional[str] = None
    domain: Optional[str] = None


class AuditLogger:
    """Writes structured JSON log entries to Logs/YYYY-MM-DD.json.

    Each call to .log() appends a new entry to today's log file.
    The log file is a JSON array that remains valid after each write.
    """

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self._logs_dir = self.vault_path / "Logs"

    def log(self, entry: LogEntry) -> None:
        """Append an audit log entry to today's log file.

        Args:
            entry: The LogEntry to record.
        """
        self._logs_dir.mkdir(exist_ok=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = self._logs_dir / f"{today}.json"

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": now,
            "action_type": entry.action_type,
            "source": entry.source,
            "status": entry.status,
            "approval_status": entry.approval_status,
        }

        if entry.target_file:
            record["target_file"] = entry.target_file
        if entry.details:
            record["details"] = entry.details
        if entry.duration_ms is not None:
            record["duration_ms"] = entry.duration_ms
        if entry.error:
            record["error"] = entry.error
        if entry.workflow_id:
            record["workflow_id"] = entry.workflow_id
        if entry.mcp_server:
            record["mcp_server"] = entry.mcp_server
        if entry.retry_count is not None:
            record["retry_count"] = entry.retry_count
        if entry.error_message:
            record["error_message"] = entry.error_message
        if entry.domain:
            record["domain"] = entry.domain

        # Read existing entries (or start fresh)
        if log_file.exists():
            try:
                existing = json.loads(log_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = []
        else:
            existing = []

        existing.append(record)

        try:
            log_file.write_text(
                json.dumps(existing, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            _py_logger.error("Failed to write audit log: %s", e)

    def get_recent(self, count: int = 5) -> list[dict]:
        """Return the most recent log entries (newest first).

        Args:
            count: Maximum number of entries to return.

        Returns:
            List of log entry dicts, newest first.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = self._logs_dir / f"{today}.json"

        if not log_file.exists():
            return []

        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
            return list(reversed(entries[-count:]))
        except (json.JSONDecodeError, OSError):
            return []
