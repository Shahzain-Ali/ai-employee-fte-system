"""T009: Unit tests for Dashboard.md template."""
import pytest
from pathlib import Path
from src.utils.vault_init import create_vault, create_vault_files


def test_dashboard_created(tmp_path: Path):
    """Dashboard.md must be created during vault setup."""
    create_vault(tmp_path)
    create_vault_files(tmp_path)
    assert (tmp_path / "Dashboard.md").is_file()


def test_dashboard_contains_required_sections(tmp_path: Path):
    """Dashboard.md must contain Status, Current Stats, and Recent Activity."""
    create_vault(tmp_path)
    create_vault_files(tmp_path)
    content = (tmp_path / "Dashboard.md").read_text()
    assert "Status" in content
    assert "Pending Tasks" in content
    assert "Awaiting Approval" in content
    assert "Completed Today" in content
    assert "Recent Activity" in content


def test_dashboard_has_no_unresolved_placeholders(tmp_path: Path):
    """Dashboard.md must not contain {{PLACEHOLDER}} markers."""
    create_vault(tmp_path)
    create_vault_files(tmp_path)
    content = (tmp_path / "Dashboard.md").read_text()
    assert "{{" not in content
    assert "}}" not in content
