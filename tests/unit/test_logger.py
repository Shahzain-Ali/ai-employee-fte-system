"""T055: Unit tests for audit logger."""
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone
from src.utils.logger import AuditLogger, LogEntry


def test_log_entry_written_to_file(temp_vault: Path):
    """Logger must write a valid JSON entry to Logs/YYYY-MM-DD.json."""
    logger = AuditLogger(vault_path=temp_vault)
    logger.log(LogEntry(
        action_type="file_detected",
        source="filesystem_watcher",
        status="success",
        target_file="Inbox/test.pdf",
    ))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = temp_vault / "Logs" / f"{today}.json"
    assert log_file.exists()

    entries = json.loads(log_file.read_text())
    assert isinstance(entries, list)
    assert len(entries) == 1


def test_log_entry_has_required_fields(temp_vault: Path):
    """Log entry must have id, timestamp, action_type, source, status."""
    logger = AuditLogger(vault_path=temp_vault)
    logger.log(LogEntry(
        action_type="processing_completed",
        source="claude_code",
        status="success",
        target_file="Done/FILE_test.pdf.md",
        details={"skill_used": "process_document"},
    ))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = temp_vault / "Logs" / f"{today}.json"
    entries = json.loads(log_file.read_text())
    entry = entries[0]

    assert "id" in entry
    assert "timestamp" in entry
    assert "action_type" in entry
    assert "source" in entry
    assert "status" in entry


def test_multiple_logs_appended(temp_vault: Path):
    """Multiple log calls must append to the same file."""
    logger = AuditLogger(vault_path=temp_vault)
    logger.log(LogEntry(action_type="file_detected", source="filesystem_watcher", status="success"))
    logger.log(LogEntry(action_type="processing_started", source="orchestrator", status="success"))
    logger.log(LogEntry(action_type="processing_completed", source="claude_code", status="success"))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = temp_vault / "Logs" / f"{today}.json"
    entries = json.loads(log_file.read_text())
    assert len(entries) == 3


def test_log_file_is_valid_json(temp_vault: Path):
    """Log file must always be valid parseable JSON."""
    logger = AuditLogger(vault_path=temp_vault)
    for i in range(5):
        logger.log(LogEntry(
            action_type="file_detected",
            source="filesystem_watcher",
            status="success",
            target_file=f"Inbox/file_{i}.pdf",
        ))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = temp_vault / "Logs" / f"{today}.json"
    # Should not raise
    data = json.loads(log_file.read_text())
    assert isinstance(data, list)
