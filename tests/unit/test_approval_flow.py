"""T047: Unit tests for approval/rejection handling."""
import pytest
from pathlib import Path
from src.utils.approval import create_approval_file
from src.orchestrator.approval_watcher import ApprovalWatcher


def test_approved_file_triggers_callback(temp_vault: Path):
    """Moving approval file to Approved/ must trigger the approved callback."""
    approved_calls = []

    approval_path = create_approval_file(
        vault_path=temp_vault,
        action_type="payment",
        source_action_file="Needs_Action/FILE_invoice.pdf.md",
        reason="Test approval",
        details={"amount": 50.00},
    )

    watcher = ApprovalWatcher(vault_path=temp_vault)
    watcher.on_approved = lambda p: approved_calls.append(p)

    # Simulate owner moving file to Approved/
    approved_dest = temp_vault / "Approved" / approval_path.name
    approval_path.rename(approved_dest)
    watcher._handle_decision(approved_dest)

    assert len(approved_calls) == 1
    assert approved_calls[0] == approved_dest


def test_rejected_file_triggers_callback(temp_vault: Path):
    """Moving approval file to Rejected/ must trigger the rejected callback."""
    rejected_calls = []

    approval_path = create_approval_file(
        vault_path=temp_vault,
        action_type="email_send",
        source_action_file="Needs_Action/FILE_draft.md",
        reason="Test rejection",
        details={"to": "test@example.com"},
    )

    watcher = ApprovalWatcher(vault_path=temp_vault)
    watcher.on_rejected = lambda p: rejected_calls.append(p)

    # Simulate owner moving file to Rejected/
    rejected_dest = temp_vault / "Rejected" / approval_path.name
    approval_path.rename(rejected_dest)
    watcher._handle_decision(rejected_dest)

    assert len(rejected_calls) == 1


def test_decision_requires_approval_file_prefix(temp_vault: Path):
    """Only APPROVAL_*.md files should trigger decision callbacks."""
    approved_calls = []

    watcher = ApprovalWatcher(vault_path=temp_vault)
    watcher.on_approved = lambda p: approved_calls.append(p)

    # Drop a random file in Approved/ — should be ignored
    random_file = temp_vault / "Approved" / "random.md"
    random_file.write_text("not an approval")
    watcher._handle_decision(random_file)

    assert len(approved_calls) == 0
