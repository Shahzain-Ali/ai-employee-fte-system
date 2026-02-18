"""File System Watcher — monitors Inbox/ and creates Needs_Action/ files."""
import threading
import logging
from pathlib import Path
from typing import Optional, Callable

from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from src.watchers.base_watcher import BaseWatcher
from src.utils.logger import AuditLogger, LogEntry
from src.watchers.action_file import (
    create_action_file,
    create_rejected_file,
    is_allowed_file_type,
    is_already_processed,
)

logger = logging.getLogger(__name__)

# Filename prefixes/suffixes to skip (partial downloads, temp files, hidden)
SKIP_PREFIXES = (".", "~")
SKIP_SUFFIXES = (".tmp", ".crdownload", ".part", ".download")


class _InboxEventHandler(FileSystemEventHandler):
    """watchdog event handler for Inbox/ folder changes."""

    def __init__(self, watcher: "FilesystemWatcher"):
        super().__init__()
        self._watcher = watcher

    def on_created(self, event):
        if not event.is_directory:
            self._watcher._handle_new_file(Path(event.src_path))


class FilesystemWatcher(BaseWatcher):
    """Watches Inbox/ for new files and creates action files in Needs_Action/.

    On startup, scans Inbox/ for any files that arrived while the watcher
    was offline (missed events). This ensures no files are skipped.
    """

    def __init__(self, vault_path: Path):
        super().__init__(vault_path)
        self._observer: Optional[Observer] = None
        self._inbox = self.vault_path / "Inbox"
        self._audit = AuditLogger(vault_path=vault_path)

    def start(self) -> None:
        """Start the watchdog observer and run startup scan."""
        logger.info("Starting FilesystemWatcher on %s", self._inbox)
        self._startup_scan()

        handler = _InboxEventHandler(self)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._inbox), recursive=False)
        self._observer.start()
        logger.info("FilesystemWatcher running")

    def stop(self) -> None:
        """Stop the watchdog observer."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join()
            logger.info("FilesystemWatcher stopped")

    def _startup_scan(self) -> None:
        """Process any files already in Inbox/ that were missed while offline."""
        if not self._inbox.exists():
            return
        for file_path in self._inbox.iterdir():
            if file_path.is_file():
                self._handle_new_file(file_path)

    def _handle_new_file(self, file_path: Path) -> None:
        """Process a new file detected in Inbox/.

        This is the core routing logic:
        - Skip hidden/temp files
        - Reject disallowed file types
        - Create action files for allowed types
        - Call on_new_file callback if set

        Args:
            file_path: Path to the newly detected file.
        """
        # Only process files that are inside Inbox/
        inbox = self.vault_path / "Inbox"
        try:
            file_path.relative_to(inbox)
        except ValueError:
            return  # Not in Inbox/, skip

        name = file_path.name

        # Skip hidden and temp files
        if name.startswith(SKIP_PREFIXES):
            logger.debug("Skipping hidden/temp file: %s", name)
            return
        if name.endswith(SKIP_SUFFIXES):
            logger.debug("Skipping temp file: %s", name)
            return

        # Industry standard: skip files already processed in a previous run
        if is_already_processed(file_path, self.vault_path):
            logger.debug("Already processed, skipping: %s", name)
            return

        logger.info("New file detected in Inbox/: %s", name)
        self._audit.log(LogEntry(
            action_type="file_detected",
            source="filesystem_watcher",
            status="success",
            target_file=f"Inbox/{name}",
        ))

        if is_allowed_file_type(file_path):
            action_path = create_action_file(file_path, self.vault_path)
            logger.info("Action file created: %s", action_path.name)
            self._audit.log(LogEntry(
                action_type="action_file_created",
                source="filesystem_watcher",
                status="success",
                target_file=f"Needs_Action/{action_path.name}",
                details={"original_file": f"Inbox/{name}"},
            ))
        else:
            reason = f"File type '{file_path.suffix}' is not supported. Executable and unknown file types are rejected."
            rejected_path = create_rejected_file(file_path, self.vault_path, reason=reason)
            logger.warning("File rejected: %s → %s", name, rejected_path.name)
            self._audit.log(LogEntry(
                action_type="action_file_created",
                source="filesystem_watcher",
                status="failure",
                target_file=f"Needs_Action/{rejected_path.name}",
                details={"original_file": f"Inbox/{name}", "reason": "file_type_rejected"},
            ))

        # Notify callback (e.g. orchestrator)
        if self.on_new_file:
            self.on_new_file(file_path)
