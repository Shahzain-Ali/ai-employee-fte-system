"""Approval Watcher — monitors Approved/ and Rejected/ for owner decisions."""
import logging
from pathlib import Path
from typing import Callable, Optional

from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

logger = logging.getLogger(__name__)


class _DecisionEventHandler(FileSystemEventHandler):
    """watchdog handler for Approved/ and Rejected/ folder events."""

    def __init__(self, watcher: "ApprovalWatcher"):
        super().__init__()
        self._watcher = watcher

    def on_created(self, event):
        if not event.is_directory:
            self._watcher._handle_decision(Path(event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self._watcher._handle_decision(Path(event.dest_path))


class ApprovalWatcher:
    """Watches Approved/ and Rejected/ for owner decisions on approval files.

    Calls on_approved or on_rejected callbacks when approval files are moved.
    """

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self._approved_dir = self.vault_path / "Approved"
        self._rejected_dir = self.vault_path / "Rejected"
        self._observer: Optional[Observer] = None

        self.on_approved: Optional[Callable[[Path], None]] = None
        self.on_rejected: Optional[Callable[[Path], None]] = None

    def start(self) -> None:
        """Start watching Approved/ and Rejected/ directories."""
        handler = _DecisionEventHandler(self)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._approved_dir), recursive=False)
        self._observer.schedule(handler, str(self._rejected_dir), recursive=False)
        self._observer.start()
        logger.info("ApprovalWatcher running")

    def stop(self) -> None:
        """Stop the approval watcher."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join()

    def _handle_decision(self, file_path: Path) -> None:
        """Route file to approved or rejected callback based on parent folder.

        Only processes files whose name starts with APPROVAL_.

        Args:
            file_path: Path to the file that appeared in Approved/ or Rejected/.
        """
        if not file_path.name.startswith("APPROVAL_"):
            logger.debug("Ignoring non-approval file: %s", file_path.name)
            return

        if file_path.parent == self._approved_dir:
            logger.info("Approval granted: %s", file_path.name)
            if self.on_approved:
                self.on_approved(file_path)

        elif file_path.parent == self._rejected_dir:
            logger.info("Approval rejected: %s", file_path.name)
            if self.on_rejected:
                self.on_rejected(file_path)
