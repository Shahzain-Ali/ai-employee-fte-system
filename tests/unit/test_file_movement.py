"""T030: Unit tests for file movement to Done/."""
import pytest
from pathlib import Path
from src.orchestrator.orchestrator import Orchestrator


def test_move_to_done(temp_vault: Path, sample_action_file: Path):
    """Action file must be moved from Needs_Action/ to Done/ after processing."""
    orch = Orchestrator(vault_path=temp_vault, dry_run=True)
    orch._move_to_done(sample_action_file)

    assert not sample_action_file.exists()
    done_file = temp_vault / "Done" / sample_action_file.name
    assert done_file.exists()


def test_move_to_done_handles_name_collision(temp_vault: Path, sample_action_file: Path):
    """If Done/ already has a file with the same name, do not overwrite."""
    existing = temp_vault / "Done" / sample_action_file.name
    existing.write_text("existing content")

    orch = Orchestrator(vault_path=temp_vault, dry_run=True)
    orch._move_to_done(sample_action_file)

    # Original existing file should still exist (not overwritten)
    assert existing.read_text() == "existing content"
    # New file should have a different name (suffix with ID)
    done_files = list((temp_vault / "Done").iterdir())
    assert len(done_files) == 2
