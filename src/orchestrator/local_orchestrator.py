"""Local Orchestrator — full-access zone, approval handler, Dashboard.md single-writer."""
import os
import logging
import time
import signal
from pathlib import Path
from datetime import datetime, timezone

import yaml

from src.orchestrator.vault_manager import (
    list_tasks_by_folder, read_task_frontmatter, move_task,
)
from src.orchestrator.approval_handler import ApprovalHandler
from src.utils.logger import AuditLogger, LogEntry
from src.utils.dashboard import update_dashboard

logger = logging.getLogger(__name__)


class LocalOrchestrator:
    """Local Agent orchestrator — runs on owner's laptop.

    Full-access zone: can approve drafts, send emails, publish posts,
    access WhatsApp, banking, and write Dashboard.md (single-writer).
    """

    def __init__(self, config_path: Path, vault_path: Path):
        self.config_path = Path(config_path)
        self.vault_path = Path(vault_path)
        self.config = self._load_config()
        self._running = False
        self._poll_interval = int(os.getenv("POLL_INTERVAL", "60"))
        self._audit = AuditLogger(vault_path=vault_path)
        self._approval_handler = ApprovalHandler(vault_path=vault_path)

    def _load_config(self) -> dict:
        """Load agent configuration from YAML."""
        try:
            return yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as e:
            logger.error("Failed to load config: %s", e)
            return {"allowed_actions": ["all"]}

    def run(self) -> None:
        """Start the Local orchestrator polling loop."""
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        logger.info("Local Orchestrator started. Zone: full-access")

        # On startup: check pending approvals
        self._check_pending_approvals_on_startup()

        while self._running:
            try:
                self._poll_once()
            except Exception as e:
                logger.error("Local poll error: %s", e, exc_info=True)
            time.sleep(self._poll_interval)

    def _check_pending_approvals_on_startup(self) -> None:
        """On startup, count and log pending approvals from Cloud."""
        total_pending = 0
        for domain in ["email", "social", "invoice"]:
            files = list_tasks_by_folder(
                self.vault_path, "Pending_Approval", subfolder=domain
            )
            total_pending += len(files)

        if total_pending > 0:
            logger.info("⚡ %d pending approvals from Cloud Agent", total_pending)
            self._audit.log(LogEntry(
                action_type="pending_approvals_detected",
                source="local_orchestrator",
                status="info",
                details={"count": total_pending},
            ))

    def _poll_once(self) -> None:
        """Single poll — process Cloud updates and pending approvals."""
        # 1. Merge Cloud status updates into Dashboard.md
        self._merge_cloud_updates()

        # 2. Check for approved files (moved to Approved/ by owner)
        self._process_approved_files()

        # 3. Check for rejected files
        self._process_rejected_files()

    def _merge_cloud_updates(self) -> None:
        """Read Updates/ files from Cloud and merge into Dashboard.md.

        Single-writer rule: ONLY Local Agent writes Dashboard.md.
        """
        updates_dir = self.vault_path / "Updates"
        if not updates_dir.exists():
            return

        update_files = sorted(
            [f for f in updates_dir.iterdir() if f.is_file() and f.suffix == ".md"],
            key=lambda f: f.stat().st_mtime,
        )

        if not update_files:
            return

        # Read all updates
        cloud_actions = []
        cloud_alerts = []
        pending_approvals = []

        for uf in update_files:
            content = uf.read_text(encoding="utf-8")
            sections = self._parse_update_sections(content)
            cloud_actions.extend(sections.get("actions", []))
            cloud_alerts.extend(sections.get("alerts", []))
            pending_approvals.extend(sections.get("pending", []))

        # Update Dashboard.md with merged info
        self._update_dashboard_with_cloud_info(cloud_actions, cloud_alerts, pending_approvals)

        # Delete processed update files
        for uf in update_files:
            try:
                uf.unlink()
                logger.debug("Processed and removed update: %s", uf.name)
            except OSError:
                pass

    def _parse_update_sections(self, content: str) -> dict:
        """Parse sections from a Cloud status update file."""
        result = {"actions": [], "alerts": [], "pending": []}
        current_section = None

        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "## Actions Since Last Update":
                current_section = "actions"
            elif stripped == "## Pending Approvals":
                current_section = "pending"
            elif stripped == "## Alerts":
                current_section = "alerts"
            elif stripped.startswith("## "):
                current_section = None
            elif current_section and stripped.startswith("- ") and stripped != "- None":
                result[current_section].append(stripped[2:])

        return result

    def _update_dashboard_with_cloud_info(
        self,
        actions: list[str],
        alerts: list[str],
        pending: list[str],
    ) -> None:
        """Write Cloud info to Dashboard.md (single-writer: Local only)."""
        dashboard = self.vault_path / "Dashboard.md"

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Count current pending approvals
        total_pending = 0
        for domain in ["email", "social", "invoice"]:
            files = list_tasks_by_folder(
                self.vault_path, "Pending_Approval", subfolder=domain
            )
            total_pending += len(files)

        # Build dashboard content
        sections = [
            f"# AI Employee Dashboard\n",
            f"**Last Updated**: {now}\n",
            f"**Local Agent**: Running\n",
            f"**Pending Approvals**: {total_pending}\n",
        ]

        if alerts:
            sections.append("\n## ⚠️ Alerts\n")
            for alert in alerts:
                sections.append(f"- {alert}\n")

        if total_pending > 0:
            sections.append("\n## 📋 Pending Approvals\n")
            for domain in ["email", "social", "invoice"]:
                files = list_tasks_by_folder(
                    self.vault_path, "Pending_Approval", subfolder=domain
                )
                for f in files:
                    fm = read_task_frontmatter(f)
                    priority = fm.get("priority", "medium")
                    sections.append(f"- [{priority}] {f.name}\n")

        if actions:
            sections.append("\n## 🤖 Recent Cloud Actions\n")
            for action in actions[-10:]:  # Last 10 actions
                sections.append(f"- {action}\n")

        dashboard.write_text("".join(sections), encoding="utf-8")
        logger.info("Dashboard.md updated (single-writer: local)")

    def _process_approved_files(self) -> None:
        """Process files in Approved/ directory."""
        approved_dir = self.vault_path / "Approved"
        if not approved_dir.exists():
            return

        for f in sorted(approved_dir.iterdir(), key=lambda x: x.stat().st_mtime):
            if f.is_file() and f.suffix == ".md":
                logger.info("Processing approved: %s", f.name)
                self._approval_handler.handle_approved(f)

    def _process_rejected_files(self) -> None:
        """Process files in Rejected/ directory."""
        rejected_dir = self.vault_path / "Rejected"
        if not rejected_dir.exists():
            return

        for f in sorted(rejected_dir.iterdir(), key=lambda x: x.stat().st_mtime):
            if f.is_file() and f.suffix == ".md":
                logger.info("Processing rejected: %s", f.name)
                self._approval_handler.handle_rejected(f)
                # Move to Done with rejected status
                move_task(self.vault_path, f, "Done",
                         subfolder=self._detect_domain(f))

    @staticmethod
    def _detect_domain(task_file: Path) -> str:
        """Detect domain from task filename or frontmatter."""
        name = task_file.name.lower()
        if "email" in name:
            return "email"
        if any(x in name for x in ["facebook", "instagram", "twitter", "linkedin", "social"]):
            return "social"
        if any(x in name for x in ["invoice", "odoo", "payment"]):
            return "invoice"
        return "general"

    def _handle_shutdown(self, signum, frame) -> None:
        """Graceful shutdown."""
        logger.info("Local Orchestrator shutting down...")
        self._running = False


def main():
    """Entry point for Local Orchestrator."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    config_path = Path(os.getenv("AGENT_CONFIG", "config/local-agent.yaml"))
    vault_path = Path(os.getenv("VAULT_PATH", "vault"))

    orchestrator = LocalOrchestrator(config_path=config_path, vault_path=vault_path)
    orchestrator.run()


if __name__ == "__main__":
    main()
