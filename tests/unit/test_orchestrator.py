"""T028: Unit tests for orchestrator polling logic."""
import pytest
from pathlib import Path
from src.orchestrator.orchestrator import Orchestrator


def test_orchestrator_finds_pending_files(temp_vault: Path, sample_action_file: Path):
    """Orchestrator must find .md files in Needs_Action/ with status: pending."""
    orch = Orchestrator(vault_path=temp_vault, dry_run=True)
    pending = orch._get_pending_files()
    assert len(pending) == 1
    assert pending[0] == sample_action_file


def test_orchestrator_finds_oldest_first(temp_vault: Path):
    """Orchestrator must return files in chronological order (oldest first)."""
    import time
    f1 = temp_vault / "Needs_Action" / "FILE_a.pdf.md"
    f1.write_text("---\nstatus: pending\n---\n")
    time.sleep(0.05)
    f2 = temp_vault / "Needs_Action" / "FILE_b.pdf.md"
    f2.write_text("---\nstatus: pending\n---\n")

    orch = Orchestrator(vault_path=temp_vault, dry_run=True)
    pending = orch._get_pending_files()

    assert pending[0].name == "FILE_a.pdf.md"
    assert pending[1].name == "FILE_b.pdf.md"


def test_orchestrator_ignores_rejected_files(temp_vault: Path):
    """Orchestrator must skip REJECTED_*.md files in Needs_Action/."""
    rejected = temp_vault / "Needs_Action" / "REJECTED_virus.exe.md"
    rejected.write_text("---\nstatus: rejected\n---\n")

    orch = Orchestrator(vault_path=temp_vault, dry_run=True)
    pending = orch._get_pending_files()

    assert rejected not in pending


def test_orchestrator_ignores_non_md_files(temp_vault: Path):
    """Orchestrator must only process .md files."""
    txt = temp_vault / "Needs_Action" / "notes.txt"
    txt.write_text("just text")

    orch = Orchestrator(vault_path=temp_vault, dry_run=True)
    pending = orch._get_pending_files()

    assert txt not in pending
