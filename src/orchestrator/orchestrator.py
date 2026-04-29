"""Orchestrator — polls Needs_Action/ and triggers Claude Code for processing.

Includes automatic fallback to alternate model after repeated failures.
When Claude Code hits rate limits or errors 5 times for the same file,
the orchestrator switches to a fallback model (minimax-m2.5:cloud).
"""
import os
import re
import time
import signal
import logging
import subprocess
import uuid
from pathlib import Path
from datetime import datetime, timezone

from src.utils.logger import AuditLogger, LogEntry
from src.utils.dashboard import update_dashboard
from src.orchestrator.model_selector import load_model_config, select_model

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
        self._pending_approval = self.vault_path / "Pending_Approval"
        self._running = False
        self._poll_interval = int(os.getenv("POLL_INTERVAL", "60"))
        self._claude_timeout = int(os.getenv("CLAUDE_TIMEOUT", "300"))
        self._max_retries = int(os.getenv("MAX_RETRIES", "5"))
        self._audit = AuditLogger(vault_path=vault_path)

        # Retry tracking: filename → retry count
        self._retry_counts: dict[str, int] = {}

        # Load model config (fallback model for when Claude rate-limits)
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "local-agent.yaml"
        self._model_config = load_model_config(config_path)

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
        retries = self._retry_counts.get(file_to_process.name, 0)
        if retries > 0:
            model_info = " [FALLBACK]" if retries >= self._max_retries else ""
            logger.info("Processing: %s (retry %d/%d%s)",
                        file_to_process.name, retries, self._max_retries, model_info)
        else:
            logger.info("Processing: %s", file_to_process.name)
        self._trigger_claude(file_to_process)

    def _get_pending_files(self) -> list[Path]:
        """Return all actionable .md files in Needs_Action/ and subfolders, sorted oldest first.

        Includes: FILE_*.md (Bronze), EMAIL_*.md (Silver), WA_*.md (Silver).
        Excludes: REJECTED_*.md files.
        """
        if not self._needs_action.exists():
            return []

        prefixes = ("FILE_", "EMAIL_", "WA_", "ODOO_", "FB_", "IG_", "TW_", "LI_")
        files = []

        # Scan root Needs_Action/
        for f in self._needs_action.iterdir():
            if f.is_file() and f.suffix == ".md" and any(f.name.startswith(p) for p in prefixes):
                files.append(f)

        # Scan subfolders (email, social, invoice, general)
        for subfolder in ["email", "social", "invoice", "general"]:
            subfolder_path = self._needs_action / subfolder
            if subfolder_path.exists() and subfolder_path.is_dir():
                for f in subfolder_path.iterdir():
                    if f.is_file() and f.suffix == ".md" and any(f.name.startswith(p) for p in prefixes):
                        files.append(f)

        # Sort by creation/modification time — oldest first
        files.sort(key=lambda f: f.stat().st_mtime)
        return files

    def _trigger_claude(self, action_file: Path) -> None:
        """Invoke Claude Code to process the action file.

        WA_*.md files are routed to the approval workflow — an approval file
        is created in Pending_Approval/ with empty reply section for the user.

        In dry_run mode, skips the subprocess call and moves the file directly.
        On timeout or failure, increments retry counter. After MAX_RETRIES
        failures, switches to fallback model (e.g., minimax:m2.5:cloud via Ollama).

        Args:
            action_file: Path to the action file in Needs_Action/.
        """
        self._audit.log(LogEntry(
            action_type="processing_started",
            source="orchestrator",
            status="success",
            target_file=str(action_file.relative_to(self.vault_path)),
        ))

        # Route WA_*.md files to approval workflow (not Claude)
        if action_file.name.startswith("WA_"):
            self._create_whatsapp_approval(action_file)
            return

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

        # --- Retry tracking & model selection ---
        fname = action_file.name
        retries = self._retry_counts.get(fname, 0)
        use_fallback = retries >= self._max_retries

        if use_fallback:
            # After max retries on Claude, switch to fallback (minimax via ollama)
            model = self._model_config.get("fallback", "minimax-m2.5:cloud")
            logger.warning(
                "File %s failed %d times on Claude — switching to fallback model: %s",
                fname, retries, model,
            )
        else:
            # Primary: Claude Code (default model)
            model = self._model_config.get("primary", "claude-sonnet-4-6")
            logger.info(
                "Using Claude model: %s (attempt %d/%d)",
                model, retries + 1, self._max_retries,
            )

        skill_name = self._resolve_skill(action_file)
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / f"{skill_name}.md"
        plan_skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "plan_creator.md"
        prompt = (
            f"Read the skill instructions at {skill_path}. "
            f"Also read the plan_creator skill at {plan_skill_path}. "
            f"Then read the action file at {action_file} and execute every step in the skill. "
            f"CRITICAL: For multi-step tasks (2+), you MUST use PlanManager from src/utils/plan_manager.py. "
            f"First call pm.create_plan() to create PLAN_*.md with all steps as [ ] (incomplete). "
            f"Then execute each step ONE BY ONE — after completing each step, immediately call "
            f"pm.mark_step_complete(plan_path, step_number, note='result details') to mark it [x]. "
            f"Do NOT write the plan file manually. Do NOT mark all steps complete at once. "
            f"Write a markdown summary note to Done/SUMMARY_{action_file.stem}.md. "
            f"Update Dashboard.md and write a log entry to Logs/. "
            f"Do NOT move the action file — the orchestrator will handle that."
        )

        cmd = self._build_cmd(prompt, model)

        # Remove CLAUDECODE so the subprocess doesn't fail with "nested session" error
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        # Use project root as cwd so Claude subprocess finds .mcp.json for MCP servers
        project_root = Path(__file__).resolve().parent.parent.parent

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._claude_timeout,
                cwd=str(project_root),
                env=env,
                stdin=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                model_label = model or "default"
                logger.info(
                    "Claude completed processing %s (model=%s, retries=%d)",
                    fname, model_label, retries,
                )
                # Success — clear retry counter
                self._retry_counts.pop(fname, None)
                if action_file.exists():
                    self._move_to_done(action_file)
                self._audit.log(LogEntry(
                    action_type="processing_completed",
                    source="orchestrator",
                    status="success",
                    target_file=f"Done/{fname}",
                    details={"model": model_label, "retries": retries},
                ))
                update_dashboard(self.vault_path)
                logger.info("Dashboard.md updated")
            else:
                self._retry_counts[fname] = retries + 1
                model_label = model or "default"
                logger.error(
                    "Claude returned error for %s (model=%s, retry %d/%d): %s",
                    fname, model_label,
                    self._retry_counts[fname], self._max_retries,
                    result.stderr[:500],
                )
                self._audit.log(LogEntry(
                    action_type="processing_failed",
                    source="orchestrator",
                    status="failure",
                    target_file=str(action_file.relative_to(self.vault_path)),
                    details={
                        "model": model_label,
                        "retry": self._retry_counts[fname],
                        "max_retries": self._max_retries,
                        "error": result.stderr[:300],
                    },
                ))
        except subprocess.TimeoutExpired:
            self._retry_counts[fname] = retries + 1
            logger.error(
                "Claude timed out after %ds for %s (retry %d/%d)",
                self._claude_timeout, fname,
                self._retry_counts[fname], self._max_retries,
            )
        except FileNotFoundError:
            logger.error("Claude Code not found. Install with: npm install -g @anthropic-ai/claude-code")

    def _build_cmd(self, prompt: str, model: str | None = None) -> list[str]:
        """Build the Claude CLI command with optional model override.

        Always includes --mcp-config to ensure MCP servers (fte-email,
        fte-odoo, fte-whatsapp, etc.) are available in the subprocess.

        Args:
            prompt: The prompt to send to Claude.
            model: Optional model identifier. If None, uses Claude default.

        Returns:
            Command list for subprocess.run().
        """
        project_root = Path(__file__).resolve().parent.parent.parent
        mcp_config = str(project_root / ".mcp.json")

        cmd = ["claude", "--print", "--dangerously-skip-permissions",
               "--mcp-config", mcp_config]
        if model:
            cmd.extend(["--model", model])
        cmd.append(prompt)
        return cmd

    def _create_whatsapp_approval(self, action_file: Path) -> None:
        """Create an approval file for WhatsApp reply in Pending_Approval/.

        Reads the WA_*.md action file, extracts sender and messages,
        creates APPROVAL_whatsapp_reply_*.md with empty reply section,
        then moves the original to Done/.

        Args:
            action_file: Path to WA_*.md in Needs_Action/.
        """
        self._pending_approval.mkdir(exist_ok=True)

        content = action_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Parse sender_name from frontmatter
        sender_name = ""
        chat_type = "individual"
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("sender_name:"):
                sender_name = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("chat_type:"):
                chat_type = stripped.split(":", 1)[1].strip()
            elif stripped == "---" and sender_name:
                break

        # Extract messages section from body
        messages_section = ""
        in_messages = False
        for line in lines:
            stripped = line.strip()
            if stripped == "## Messages":
                in_messages = True
                continue
            if in_messages:
                if stripped.startswith("##"):
                    break
                messages_section += line + "\n"

        messages_section = messages_section.strip()

        # Extract keywords
        keywords_str = ""
        for line in lines:
            if line.strip().startswith("**Keywords Matched**"):
                keywords_str = line.split(":", 1)[1].strip() if ":" in line else ""
                break

        now = datetime.now(timezone.utc)
        ts_compact = now.strftime("%Y%m%dT%H%M%SZ")
        iso_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        entry_id = str(uuid.uuid4())

        filename = f"APPROVAL_whatsapp_reply_{ts_compact}.md"
        approval_path = self._pending_approval / filename

        approval_content = f"""---
id: {entry_id}
type: approval_request
action_type: whatsapp_reply
status: pending
sender_name: {sender_name}
chat_type: {chat_type}
created_at: {iso_now}
source_action_file: Needs_Action/{action_file.name}
details:
  sender_name: {sender_name}
  reply_message:
---

# WhatsApp Reply Approval: {sender_name}

## Original Messages

{messages_section}

**Keywords Matched**: {keywords_str}

## Your Reply

> Write your reply below this line:



## Instructions

To **APPROVE**: Write your reply above, then move this file to `Approved/`
To **REJECT**: Move this file to `Rejected/`
"""
        approval_path.write_text(approval_content, encoding="utf-8")

        logger.info(
            "Created WhatsApp approval: %s (sender: %s)",
            filename, sender_name,
        )

        self._audit.log(LogEntry(
            action_type="whatsapp_approval_created",
            source="orchestrator",
            status="success",
            target_file=f"Pending_Approval/{filename}",
            details={
                "sender": sender_name,
                "source_file": action_file.name,
            },
        ))

        # Move original WA file to Done/
        self._move_to_done(action_file)
        update_dashboard(self.vault_path)

    @staticmethod
    def _resolve_skill(action_file: Path) -> str:
        """Determine which Agent Skill to use based on action file prefix.

        Args:
            action_file: Path to the action file in Needs_Action/.

        Returns:
            Skill filename (without .md extension).
        """
        name = action_file.name
        if name.startswith("EMAIL_"):
            return "email_responder"
        if name.startswith("WA_"):
            return "whatsapp_handler"
        if name.startswith("ODOO_"):
            return "odoo_accountant"
        if name.startswith("FB_"):
            return "facebook_poster"
        if name.startswith("IG_"):
            return "instagram_manager"
        if name.startswith("TW_"):
            return "twitter_poster"
        if name.startswith("LI_"):
            return "linkedin_poster"
        return "process_document"

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
