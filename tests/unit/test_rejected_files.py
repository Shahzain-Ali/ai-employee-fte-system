"""T019: Unit tests for rejected file handling."""
import pytest
from pathlib import Path
from src.watchers.action_file import create_action_file, create_rejected_file, is_allowed_file_type


def test_executable_files_are_rejected(temp_vault: Path):
    """Files with executable extensions must be rejected."""
    for ext in [".exe", ".bat", ".sh", ".cmd", ".ps1"]:
        f = temp_vault / "Inbox" / f"malware{ext}"
        f.write_bytes(b"bad")
        assert not is_allowed_file_type(f), f"{ext} should be rejected"


def test_allowed_files_pass(temp_vault: Path):
    """PDF, images, and documents must be allowed."""
    for ext in [".pdf", ".png", ".jpg", ".jpeg", ".docx", ".txt", ".md", ".csv"]:
        f = temp_vault / "Inbox" / f"file{ext}"
        f.write_bytes(b"data")
        assert is_allowed_file_type(f), f"{ext} should be allowed"


def test_rejected_file_created_in_needs_action(temp_vault: Path):
    """Rejected files must produce a REJECTED_*.md in Needs_Action/."""
    source = temp_vault / "Inbox" / "virus.exe"
    source.write_bytes(b"bad")

    rejected_path = create_rejected_file(source, temp_vault, reason="Executable files are not allowed")

    assert rejected_path.exists()
    assert rejected_path.parent == temp_vault / "Needs_Action"
    assert rejected_path.name.startswith("REJECTED_")
    assert rejected_path.suffix == ".md"


def test_rejected_file_contains_reason(temp_vault: Path):
    """Rejected file must contain the rejection reason."""
    source = temp_vault / "Inbox" / "virus.exe"
    source.write_bytes(b"bad")

    rejected_path = create_rejected_file(source, temp_vault, reason="Executable files are not allowed")
    content = rejected_path.read_text()

    assert "Executable files are not allowed" in content
    assert "REJECTED" in content
