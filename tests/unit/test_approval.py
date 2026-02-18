"""T046: Unit tests for approval file creation."""
import pytest
from pathlib import Path
from src.utils.approval import create_approval_file, ALLOWED_ACTION_TYPES


def test_approval_file_created_in_pending(temp_vault: Path):
    """Approval file must be created in Pending_Approval/."""
    path = create_approval_file(
        vault_path=temp_vault,
        action_type="payment",
        source_action_file="Needs_Action/FILE_invoice.pdf.md",
        reason="Payment requires human approval",
        details={"amount": 150.00, "recipient": "Vendor"},
    )
    assert path.exists()
    assert path.parent == temp_vault / "Pending_Approval"


def test_approval_file_has_approval_prefix(temp_vault: Path):
    """Approval filename must start with APPROVAL_."""
    path = create_approval_file(
        vault_path=temp_vault,
        action_type="payment",
        source_action_file="Needs_Action/FILE_invoice.pdf.md",
        reason="Requires approval",
        details={},
    )
    assert path.name.startswith("APPROVAL_")


def test_approval_file_contains_required_frontmatter(temp_vault: Path):
    """Approval file must contain required YAML frontmatter."""
    path = create_approval_file(
        vault_path=temp_vault,
        action_type="email_send",
        source_action_file="Needs_Action/FILE_draft.md",
        reason="Email to new contact",
        details={"to": "new@example.com"},
    )
    content = path.read_text()
    assert "type: approval_request" in content
    assert "status: pending" in content
    assert "action_type:" in content
    assert "created_at:" in content


def test_approval_file_contains_reason(temp_vault: Path):
    """Approval file body must contain the reason."""
    path = create_approval_file(
        vault_path=temp_vault,
        action_type="file_delete",
        source_action_file="Needs_Action/FILE_old.txt.md",
        reason="File deletion requires explicit approval",
        details={"file": "important_data.txt"},
    )
    content = path.read_text()
    assert "File deletion requires explicit approval" in content


def test_invalid_action_type_raises(temp_vault: Path):
    """Invalid action_type must raise ValueError."""
    with pytest.raises(ValueError, match="action_type"):
        create_approval_file(
            vault_path=temp_vault,
            action_type="invalid_type",
            source_action_file="Needs_Action/FILE_test.md",
            reason="test",
            details={},
        )
