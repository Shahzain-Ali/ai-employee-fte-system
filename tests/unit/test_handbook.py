"""T010: Unit tests for Company_Handbook.md validation."""
import pytest
from pathlib import Path
from src.utils.vault_init import create_vault, create_vault_files


def test_handbook_created(tmp_path: Path):
    """Company_Handbook.md must be created during vault setup."""
    create_vault(tmp_path)
    create_vault_files(tmp_path)
    assert (tmp_path / "Company_Handbook.md").is_file()


def test_handbook_contains_approval_rules(tmp_path: Path):
    """Handbook must explicitly list approval-required actions."""
    create_vault(tmp_path)
    create_vault_files(tmp_path)
    content = (tmp_path / "Company_Handbook.md").read_text()
    assert "Approval Requirements" in content
    assert "Payments" in content
    assert "Emails" in content
    assert "File Deletions" in content


def test_handbook_contains_forbidden_actions(tmp_path: Path):
    """Handbook must list forbidden actions."""
    create_vault(tmp_path)
    create_vault_files(tmp_path)
    content = (tmp_path / "Company_Handbook.md").read_text()
    assert "Forbidden Actions" in content


def test_handbook_references_pending_approval(tmp_path: Path):
    """Handbook must reference Pending_Approval/ folder for HITL workflow."""
    create_vault(tmp_path)
    create_vault_files(tmp_path)
    content = (tmp_path / "Company_Handbook.md").read_text()
    assert "Pending_Approval" in content
