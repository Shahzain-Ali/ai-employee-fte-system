"""Orchestrator — polls Needs_Action/ and triggers Claude Code for processing."""
import os
import time
import signal
import logging
import subprocess
import uuid
from pathlib import Path

from src.utils.logger import AuditLogger, LogEntry
from src.utils.dashboard import update_dashboard

logger = logging.getLogger(__name__)


class Orchestrator:
    """Polls Needs_Action/ and triggers Claude Code for each action file.

    Processes files chronologically (oldest first). In dry_run mode,
    Claude Code is not invoked — files are simply moved to Done/.
    """

    def __init__(self, vault_path: Path, dry_run: bool = True):
        self.vault_path = Path(vault_path)
        self.dry_run = dry_run
        self._needs_action = self.vault_path / "Needs_Action"
        self._done = self.vault_path / "Done"
        self._running = False
        self._poll_interval = int(os.getenv("POLL_INTERVAL", "60"))
        self._claude_timeout = int(os.getenv("CLAUDE_TIMEOUT", "300"))
        self._audit = AuditLogger(vault_path=vault_path)

    def run(self) -> None:
        """Start the polling loop. Blocks until stopped."""
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        logger.info("Orchestrator started. Poll interval: %ds, dry_run=%s",
                    self._poll_interval, self.dry_run)

        while self._running:
            try:
                self._poll_once()
            except Exception as e:
                logger.error("Orchestrator poll error: %s", e, exc_info=True)
            time.sleep(self._poll_interval)

    def _poll_once(self) -> None:
        """Single poll — process one pending file if found."""
        pending = self._get_pending_files()
        if not pending:
            logger.debug("No pending files in Needs_Action/")
            return

        file_to_process = pending[0]
        logger.info("Processing: %s", file_to_process.name)
        self._trigger_claude(file_to_process)

    def _get_pending_files(self) -> list[Path]:
        """Return all FILE_*.md files in Needs_Action/, sorted oldest first.

        Excludes REJECTED_*.md files.
        """
        if not self._needs_action.exists():
            return []

        files = [
            f for f in self._needs_action.iterdir()
            if f.is_file()
            and f.suffix == ".md"
            and f.name.startswith("FILE_")
        ]
        # Sort by creation/modification time — oldest first
        files.sort(key=lambda f: f.stat().st_mtime)
        return files

    def _trigger_claude(self, action_file: Path) -> None:
        """Invoke Claude Code to process the action file.

        In dry_run mode, skips the subprocess call and moves the file directly.
        On timeout or failure, leaves the file in Needs_Action/ for retry.

        Args:
            action_file: Path to the action file in Needs_Action/.
        """
        self._audit.log(LogEntry(
            action_type="processing_started",
            source="orchestrator",
            status="success",
            target_file=str(action_file.relative_to(self.vault_path)),
        ))

        if self.dry_run:
            logger.info("[DRY_RUN] Would trigger Claude for %s", action_file.name)
            self._move_to_done(action_file)
            self._audit.log(LogEntry(
                action_type="processing_completed",
                source="orchestrator",
                status="success",
                target_file=f"Done/{action_file.name}",
                details={"dry_run": True},
            ))
            update_dashboard(self.vault_path)
            logger.info("Dashboard.md updated")
            return

        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "process_document.md"
        prompt = (
            f"Read the skill instructions at {skill_path}. "
            f"Then read the action file at {action_file} and execute every step in the skill. "
            f"Write a markdown summary note to Done/SUMMARY_{action_file.stem}.md. "
            f"Update Dashboard.md and write a log entry to Logs/. "
            f"Do NOT move the action file — the orchestrator will handle that."
        )

        cmd = ["claude", "--print", "--dangerously-skip-permissions", prompt]

        # Remove CLAUDECODE so the subprocess doesn't fail with "nested session" error
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._claude_timeout,
                cwd=str(self.vault_path),
                env=env,
            )
            if result.returncode == 0:
                logger.info("Claude completed processing %s", action_file.name)
                if action_file.exists():
                    self._move_to_done(action_file)
                self._audit.log(LogEntry(
                    action_type="processing_completed",
                    source="orchestrator",
                    status="success",
                    target_file=f"Done/{action_file.name}",
                ))
                update_dashboard(self.vault_path)
                logger.info("Dashboard.md updated")
            else:
                logger.error(
                    "Claude returned error for %s: %s",
                    action_file.name,
                    result.stderr[:500],
                )
        except subprocess.TimeoutExpired:
            logger.error(
                "Claude timed out after %ds for %s",
                self._claude_timeout,
                action_file.name,
            )
        except FileNotFoundError:
            logger.error("Claude Code not found. Install with: npm install -g @anthropic-ai/claude-code")

    def _move_to_done(self, action_file: Path) -> None:
        """Move an action file from Needs_Action/ to Done/.

        Handles name collisions by appending a short UUID.

        Args:
            action_file: Path to the file in Needs_Action/.
        """
        target = self._done / action_file.name

        if target.exists():
            short_id = str(uuid.uuid4())[:8]
            stem = action_file.stem
            target = self._done / f"{stem}_{short_id}.md"

        action_file.rename(target)
        logger.info("Moved %s → Done/%s", action_file.name, target.name)

    def _handle_shutdown(self, signum, frame) -> None:
        """Handle graceful shutdown on SIGTERM/SIGINT."""
        logger.info("Shutdown signal received. Stopping orchestrator...")
        self._running = False
