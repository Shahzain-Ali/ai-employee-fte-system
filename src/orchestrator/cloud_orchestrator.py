"""Cloud Orchestrator — draft-only zone, polls vault, creates drafts via Claude Code."""
import os
import logging
import subprocess
import time
import signal
from pathlib import Path
from datetime import datetime, timezone

import yaml

from src.orchestrator.vault_manager import (
    claim_task, list_tasks_by_folder, read_task_frontmatter,
    move_task, write_status_update,
)
from src.orchestrator.model_selector import load_model_config, select_model
from src.utils.logger import AuditLogger, LogEntry

logger = logging.getLogger(__name__)


class ZoneViolationError(Exception):
    """Raised when Cloud Agent attempts a forbidden action."""


class CloudOrchestrator:
    """Cloud Agent orchestrator — runs 24/7, creates drafts only.

    Zone enforcement: Cloud cannot send emails, publish social posts,
    confirm payments, write Dashboard.md, or access WhatsApp/banking.
    """

    def __init__(self, config_path: Path, vault_path: Path):
        self.config_path = Path(config_path)
        self.vault_path = Path(vault_path)
        self.config = self._load_config()
        self._running = False
        self._poll_interval = int(os.getenv("POLL_INTERVAL", "60"))
        self._claude_timeout = int(os.getenv("CLAUDE_TIMEOUT", "300"))
        self._audit = AuditLogger(vault_path=vault_path)
        self._actions_since_update: list[str] = []
        self._last_status_update = time.time()
        self._status_interval = self.config.get("status_update_interval", 1800)

        # Rate limiting
        self._drafts_this_hour: list[float] = []
        rate_limits = self.config.get("rate_limits", {})
        self._max_drafts_per_hour = rate_limits.get("max_drafts_per_hour", 20)

        # Retry tracking — after 3 fails, switch to fallback model
        self._retry_counts: dict[str, int] = {}
        self._max_retries_before_fallback = 3

    def _load_config(self) -> dict:
        """Load agent configuration from YAML."""
        try:
            return yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as e:
            logger.error("Failed to load config: %s", e)
            return {"forbidden_actions": [], "allowed_actions": []}

    def run(self) -> None:
        """Start the Cloud orchestrator polling loop."""
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        logger.info(
            "Cloud Orchestrator started. Zone: %s, Poll: %ds",
            self.config.get("zone", "draft-only"), self._poll_interval,
        )

        while self._running:
            try:
                self._poll_once()
                self._maybe_write_status_update()
            except Exception as e:
                logger.error("Cloud poll error: %s", e, exc_info=True)
            time.sleep(self._poll_interval)

    def _poll_once(self) -> None:
        """Single poll — check all Needs_Action subfolders for tasks."""
        domains = ["email", "social", "invoice", "general"]

        for domain in domains:
            tasks = list_tasks_by_folder(self.vault_path, "Needs_Action", subfolder=domain)
            if not tasks:
                continue

            task_file = tasks[0]  # Process oldest first
            logger.info("Cloud processing: %s", task_file.name)

            try:
                self._process_task(task_file, domain)
            except ZoneViolationError as e:
                logger.error("ZONE VIOLATION: %s", e)
                self._audit.log(LogEntry(
                    action_type="zone_violation",
                    source="cloud_orchestrator",
                    status="blocked",
                    target_file=str(task_file.relative_to(self.vault_path)),
                    error=str(e),
                ))

    def _process_task(self, task_file: Path, domain: str) -> None:
        """Process a single task — claim, draft, move to Pending_Approval.

        Args:
            task_file: Path to the task in Needs_Action/<domain>/.
            domain: Task domain (email, social, invoice, general).
        """
        # Rate limit check
        if not self._check_rate_limit():
            logger.warning("Rate limit reached — skipping task")
            return

        # Claim the task
        try:
            claimed = claim_task(self.vault_path, task_file, agent="cloud")
        except FileNotFoundError:
            logger.info("Task already claimed: %s", task_file.name)
            return

        self._audit.log(LogEntry(
            action_type="task_claimed",
            source="cloud_orchestrator",
            status="success",
            target_file=str(claimed.relative_to(self.vault_path)),
        ))

        # Read task content and select model
        frontmatter = read_task_frontmatter(claimed)
        task_content = claimed.read_text(encoding="utf-8")
        task_type = frontmatter.get("type", "")

        # Check retry count — after 3 fails, switch to fallback model
        retry_count = self._retry_counts.get(task_file.name, 0)

        if retry_count >= self._max_retries_before_fallback:
            model_config = load_model_config(self.config_path)
            model = model_config.get("fallback", "minimax:m2.5:cloud")
            logger.warning(
                "Task %s failed %d times — switching to fallback model: %s",
                task_file.name, retry_count, model,
            )
        else:
            model = select_model(
                self.config_path,
                task_type=task_type,
                task_content=task_content,
                skip_quota_check=True,
            )

        # Invoke Claude Code to create draft
        success = self._invoke_claude_draft(claimed, domain, model)

        if success:
            # Reset retry count on success
            self._retry_counts.pop(task_file.name, None)
            # Move to Pending_Approval/<domain>/
            new_path = move_task(self.vault_path, claimed, "Pending_Approval", subfolder=domain)
            self._actions_since_update.append(
                f"Drafted {task_type} for {domain}: {task_file.name}"
            )
            self._drafts_this_hour.append(time.time())

            self._audit.log(LogEntry(
                action_type="draft_created",
                source="cloud_orchestrator",
                status="success",
                target_file=str(new_path.relative_to(self.vault_path)),
                details={"model": model, "domain": domain},
            ))
        else:
            # Increment retry count
            self._retry_counts[task_file.name] = retry_count + 1
            logger.warning(
                "Draft failed for %s (attempt %d/%d)",
                task_file.name, retry_count + 1, self._max_retries_before_fallback,
            )
            # Move back to Needs_Action/<domain>/ for retry on next poll
            try:
                move_task(self.vault_path, claimed, "Needs_Action", subfolder=domain)
            except Exception as e:
                logger.error("Failed to move %s back to Needs_Action: %s", claimed.name, e)

    def _invoke_claude_draft(self, task_file: Path, domain: str, model: str) -> bool:
        """Invoke Claude Code CLI to create a draft for the task.

        Args:
            task_file: Path to the claimed task file.
            domain: Task domain.
            model: Model identifier to use.

        Returns:
            True if draft created successfully.
        """
        skill_name = self._resolve_skill(domain)
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / f"{skill_name}.md"

        prompt = (
            f"Read the skill at {skill_path}. "
            f"Read the task at {task_file}. "
            f"Create a DRAFT response — do NOT send, publish, or execute any final action. "
            f"Write the draft content into the task file under a '## Draft Reply' or '## Draft Post' section. "
            f"Do NOT call send_email_tool, create_page_post, create_ig_post, post_tweet, or any publish action."
        )

        cmd = ["claude", "--print", "--dangerously-skip-permissions"]
        if model and not model.startswith("minimax"):
            cmd.extend(["--model", model])
        cmd.append(prompt)

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        project_root = Path(__file__).resolve().parent.parent.parent

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                stdin=subprocess.DEVNULL,
                timeout=self._claude_timeout, cwd=str(project_root), env=env,
            )
            if result.returncode == 0:
                logger.info("Claude drafted: %s (model: %s)", task_file.name, model)
                return True
            else:
                logger.error("Claude draft failed: %s", result.stderr[:300])
                return False
        except subprocess.TimeoutExpired:
            logger.error("Claude draft timed out for %s", task_file.name)
            return False
        except FileNotFoundError:
            logger.error("Claude Code CLI not found")
            return False

    def enforce_zone(self, action: str) -> None:
        """Check if an action is allowed in the Cloud zone.

        Args:
            action: The action being attempted.

        Raises:
            ZoneViolationError: If the action is forbidden.
        """
        forbidden = self.config.get("forbidden_actions", [])
        if action in forbidden:
            raise ZoneViolationError(
                f"Action '{action}' is forbidden in Cloud zone (draft-only)"
            )

    def _check_rate_limit(self) -> bool:
        """Check if within rate limits.

        Returns:
            True if under limit, False if rate limited.
        """
        now = time.time()
        one_hour_ago = now - 3600
        self._drafts_this_hour = [t for t in self._drafts_this_hour if t > one_hour_ago]
        return len(self._drafts_this_hour) < self._max_drafts_per_hour

    def _maybe_write_status_update(self) -> None:
        """Write a status update if enough time has passed."""
        elapsed = time.time() - self._last_status_update
        if elapsed < self._status_interval and not self._actions_since_update:
            return

        if elapsed >= self._status_interval:
            # Get pending approvals
            pending = []
            for domain in ["email", "social", "invoice"]:
                files = list_tasks_by_folder(
                    self.vault_path, "Pending_Approval", subfolder=domain
                )
                pending.extend(f.name for f in files)

            write_status_update(
                vault_path=self.vault_path,
                agent="cloud",
                actions=self._actions_since_update or ["No actions since last update"],
                pending_approvals=pending or None,
            )
            self._actions_since_update = []
            self._last_status_update = time.time()

    @staticmethod
    def _resolve_skill(domain: str) -> str:
        """Map domain to Agent Skill name."""
        return {
            "email": "email_responder",
            "social": "facebook_poster",
            "invoice": "odoo_accountant",
            "general": "process_document",
        }.get(domain, "process_document")

    def _handle_shutdown(self, signum, frame) -> None:
        """Graceful shutdown."""
        logger.info("Cloud Orchestrator shutting down...")
        # Write final status update
        if self._actions_since_update:
            write_status_update(
                vault_path=self.vault_path,
                agent="cloud",
                actions=self._actions_since_update,
                alerts=["Cloud Agent shutting down"],
            )
        self._running = False


def main():
    """Entry point for Cloud Orchestrator."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    config_path = Path(os.getenv("AGENT_CONFIG", "config/cloud-agent.yaml"))
    vault_path = Path(os.getenv("VAULT_PATH", "vault"))

    orchestrator = CloudOrchestrator(config_path=config_path, vault_path=vault_path)
    orchestrator.run()


if __name__ == "__main__":
    main()
