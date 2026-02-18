"""T008: Unit tests for vault initialization."""
import pytest
from pathlib import Path
from src.utils.vault_init import create_vault


def test_create_vault_creates_all_folders(tmp_path: Path):
    """All 7 required folders must be created."""
    create_vault(tmp_path)
    expected = [
        "Inbox", "Needs_Action", "Done", "Logs",
        "Pending_Approval", "Approved", "Rejected",
    ]
    for folder in expected:
        assert (tmp_path / folder).is_dir(), f"Missing folder: {folder}"


def test_create_vault_is_idempotent(tmp_path: Path):
    """Running create_vault twice must not raise errors."""
    create_vault(tmp_path)
    create_vault(tmp_path)  # Second call should be safe
    assert (tmp_path / "Inbox").is_dir()


def test_create_vault_returns_path(tmp_path: Path):
    """create_vault must return the vault path."""
    result = create_vault(tmp_path)
    assert result == tmp_path


def test_create_vault_raises_if_not_writable(tmp_path: Path):
    """If vault path is not writable, raise PermissionError."""
    import os
    os.chmod(tmp_path, 0o444)  # Read-only
    with pytest.raises((PermissionError, OSError)):
        create_vault(tmp_path / "new_vault")
    os.chmod(tmp_path, 0o755)  # Restore
