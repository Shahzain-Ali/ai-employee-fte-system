"""Base watcher interface for all Bronze tier watchers."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional


class BaseWatcher(ABC):
    """Abstract base class for all watchers.

    Subclasses monitor a data source and call on_new_file
    when new content is ready for processing.
    """

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self.on_new_file: Optional[Callable[[Path], None]] = None

    @abstractmethod
    def start(self) -> None:
        """Start watching for new content."""

    @abstractmethod
    def stop(self) -> None:
        """Stop watching."""
