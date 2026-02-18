"""T017: Unit tests for filesystem watcher file detection."""
import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.watchers.filesystem_watcher import FilesystemWatcher


def test_watcher_detects_new_file(temp_vault: Path):
    """Watcher must detect files dropped in Inbox/."""
    detected = []
    watcher = FilesystemWatcher(vault_path=temp_vault)
    watcher.on_new_file = lambda p: detected.append(p)

    # Simulate a file event
    test_file = temp_vault / "Inbox" / "test.pdf"
    test_file.write_bytes(b"%PDF fake")
    watcher._handle_new_file(test_file)

    assert len(detected) == 1
    assert detected[0] == test_file


def test_watcher_ignores_non_inbox_files(temp_vault: Path):
    """Watcher must not process files outside Inbox/."""
    detected = []
    watcher = FilesystemWatcher(vault_path=temp_vault)
    watcher.on_new_file = lambda p: detected.append(p)

    outside_file = temp_vault / "Done" / "test.pdf"
    outside_file.write_bytes(b"data")
    watcher._handle_new_file(outside_file)

    assert len(detected) == 0


def test_watcher_ignores_hidden_files(temp_vault: Path):
    """Watcher must skip hidden/system files (starting with .)."""
    detected = []
    watcher = FilesystemWatcher(vault_path=temp_vault)
    watcher.on_new_file = lambda p: detected.append(p)

    hidden = temp_vault / "Inbox" / ".DS_Store"
    hidden.write_bytes(b"hidden")
    watcher._handle_new_file(hidden)

    assert len(detected) == 0


def test_watcher_ignores_temp_files(temp_vault: Path):
    """Watcher must skip temp files (starting with ~ or ending with .tmp)."""
    detected = []
    watcher = FilesystemWatcher(vault_path=temp_vault)
    watcher.on_new_file = lambda p: detected.append(p)

    for name in ["~invoice.pdf", "invoice.pdf.tmp", "invoice.pdf.crdownload"]:
        temp = temp_vault / "Inbox" / name
        temp.write_bytes(b"data")
        watcher._handle_new_file(temp)

    assert len(detected) == 0
