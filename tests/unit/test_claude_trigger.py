"""T029: Unit tests for Claude Code triggering."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.orchestrator.orchestrator import Orchestrator


def test_dry_run_does_not_call_subprocess(temp_vault: Path, sample_action_file: Path):
    """In dry_run mode, Claude Code must NOT be called via subprocess."""
    orch = Orchestrator(vault_path=temp_vault, dry_run=True)

    with patch("subprocess.run") as mock_run:
        orch._trigger_claude(sample_action_file)
        mock_run.assert_not_called()


def test_dry_run_marks_file_completed(temp_vault: Path, sample_action_file: Path):
    """In dry_run mode, the action file must be moved to Done/."""
    orch = Orchestrator(vault_path=temp_vault, dry_run=True)
    orch._trigger_claude(sample_action_file)

    done_dir = temp_vault / "Done"
    done_files = list(done_dir.iterdir())
    assert len(done_files) == 1
    assert done_files[0].name == sample_action_file.name


def test_trigger_builds_correct_claude_command(temp_vault: Path, sample_action_file: Path):
    """Claude trigger must pass the action file path to the claude command."""
    orch = Orchestrator(vault_path=temp_vault, dry_run=False)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        orch._trigger_claude(sample_action_file)

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "claude" in cmd[0]
        assert str(sample_action_file) in " ".join(str(a) for a in cmd)
