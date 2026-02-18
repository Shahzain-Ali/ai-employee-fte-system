"""Pytest fixtures for Bronze tier tests."""
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault directory with all required subfolders."""
    folders = [
        "Inbox",
        "Needs_Action",
        "Done",
        "Logs",
        "Pending_Approval",
        "Approved",
        "Rejected",
    ]
    for folder in folders:
        (tmp_path / folder).mkdir()
    return tmp_path


@pytest.fixture
def sample_pdf(temp_vault: Path) -> Path:
    """Drop a fake PDF file in Inbox/ for watcher tests."""
    pdf = temp_vault / "Inbox" / "invoice_test.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake pdf content")
    return pdf


@pytest.fixture
def sample_action_file(temp_vault: Path) -> Path:
    """Create a sample action file in Needs_Action/ for orchestrator tests."""
    content = """---
id: test-001
type: file_processing
status: pending
original_file: Inbox/invoice_test.pdf
file_type: application/pdf
skill: process_document
created_at: 2026-02-17T10:00:00Z
---

# Action: Process invoice_test.pdf

Process the file located at `Inbox/invoice_test.pdf`.
Use the `process_document` skill.
"""
    action = temp_vault / "Needs_Action" / "FILE_invoice_test.pdf.md"
    action.write_text(content)
    return action
