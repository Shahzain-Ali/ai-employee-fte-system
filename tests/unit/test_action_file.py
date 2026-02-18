"""T018: Unit tests for action file creation."""
import pytest
from pathlib import Path
from src.watchers.action_file import create_action_file, sanitize_filename


def test_create_action_file_for_pdf(temp_vault: Path):
    """Action file must be created in Needs_Action/ for a PDF."""
    source = temp_vault / "Inbox" / "invoice.pdf"
    source.write_bytes(b"%PDF fake")

    action_path = create_action_file(source, temp_vault)

    assert action_path.exists()
    assert action_path.parent == temp_vault / "Needs_Action"
    assert action_path.name.startswith("FILE_")
    assert action_path.suffix == ".md"


def test_action_file_has_required_frontmatter(temp_vault: Path):
    """Action file must contain required YAML frontmatter fields."""
    source = temp_vault / "Inbox" / "invoice.pdf"
    source.write_bytes(b"%PDF fake")

    action_path = create_action_file(source, temp_vault)
    content = action_path.read_text()

    assert "id:" in content
    assert "type:" in content
    assert "status: pending" in content
    assert "original_file:" in content
    assert "skill:" in content
    assert "created_at:" in content


def test_action_file_naming_convention(temp_vault: Path):
    """Action file name must follow FILE_<original_name>.md convention."""
    source = temp_vault / "Inbox" / "my document.pdf"
    source.write_bytes(b"%PDF fake")

    action_path = create_action_file(source, temp_vault)

    assert "FILE_" in action_path.name
    assert action_path.name.endswith(".md")


def test_sanitize_filename_removes_spaces():
    """Filename sanitization must replace spaces with underscores."""
    result = sanitize_filename("my file name.pdf")
    assert " " not in result


def test_sanitize_filename_removes_special_chars():
    """Filename sanitization must remove special characters."""
    result = sanitize_filename("file (1) & copy!.pdf")
    assert all(c.isalnum() or c in "._-" for c in result)
