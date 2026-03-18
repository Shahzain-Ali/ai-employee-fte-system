"""Approval Handler — executes actions after human approval."""
import logging
import uuid
from pathlib import Path

from src.utils.email_sender import send_email, parse_approval_for_email
from src.utils.whatsapp_sender import parse_approval_for_whatsapp
from src.utils.logger import AuditLogger, LogEntry
from src.utils.dashboard import update_dashboard

logger = logging.getLogger(__name__)


class ApprovalHandler:
    """Handles approved and rejected actions from the HITL workflow.

    When a file is moved to Approved/, this handler parses it and
    executes the corresponding action (e.g., send email, send WhatsApp reply).
    """

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self._audit = AuditLogger(vault_path=vault_path)
        self._done = self.vault_path / "Done"
        self._whatsapp_watcher = None  # Set by main.py when watcher is running

    def handle_approved(self, approval_file: Path) -> None:
        """Process an approved action file.

        Args:
            approval_file: Path to the APPROVAL_*.md file in Approved/.
        """
        logger.info("Handling approved action: %s", approval_file.name)

        # Try email send
        email_details = parse_approval_for_email(approval_file)
        if email_details:
            self._execute_email_send(approval_file, email_details)
            return

        # Try WhatsApp reply
        wa_details = parse_approval_for_whatsapp(approval_file)
        if wa_details:
            self._execute_whatsapp_reply(approval_file, wa_details)
            return

        # Try Gold tier approval types (Facebook, Instagram, Odoo payment)
        action_type = self._parse_action_type(approval_file)
        if action_type in ("facebook_post", "facebook_reply"):
            self._execute_gold_approval(approval_file, action_type, "facebook")
            return
        if action_type in ("instagram_post", "instagram_reel", "instagram_reply"):
            self._execute_gold_approval(approval_file, action_type, "instagram")
            return
        if action_type == "odoo_payment":
            self._execute_gold_approval(approval_file, action_type, "odoo")
            return

        logger.warning("Unknown approval type for %s — no action taken", approval_file.name)

    def handle_rejected(self, approval_file: Path) -> None:
        """Process a rejected action file.

        Args:
            approval_file: Path to the APPROVAL_*.md file in Rejected/.
        """
        logger.info("Action rejected: %s", approval_file.name)

        self._audit.log(LogEntry(
            action_type="action_rejected",
            source="approval_handler",
            status="success",
            target_file=str(approval_file.relative_to(self.vault_path)),
        ))
        update_dashboard(self.vault_path)

    def _execute_email_send(self, approval_file: Path, details: dict) -> None:
        """Send an email after approval.

        Args:
            approval_file: The approved APPROVAL_email_send_*.md file.
            details: Dict with 'to', 'subject', 'body' keys.
        """
        to = details["to"]
        subject = details["subject"]
        body = details["body"]

        try:
            result = send_email(to=to, subject=subject, body=body)

            self._audit.log(LogEntry(
                action_type="email_sent",
                source="approval_handler",
                status="success",
                target_file=str(approval_file.relative_to(self.vault_path)),
                details={
                    "to": to,
                    "subject": subject,
                    "gmail_message_id": result.get("id", ""),
                },
            ))

            # Move approval file to Done/
            done_path = self._done / approval_file.name
            approval_file.rename(done_path)
            logger.info("Email sent to %s — approval moved to Done/", to)

            update_dashboard(self.vault_path)

        except Exception as e:
            logger.error("Failed to send email to %s: %s", to, e)
            self._audit.log(LogEntry(
                action_type="email_send_failed",
                source="approval_handler",
                status="failure",
                target_file=str(approval_file.relative_to(self.vault_path)),
                error=str(e),
            ))

    def _execute_whatsapp_reply(self, approval_file: Path, details: dict) -> None:
        """Queue a WhatsApp reply to be sent by the watcher's own thread.

        Playwright is single-threaded — cannot call browser from approval watcher thread.
        Instead, we queue the reply and the watcher processes it in its own poll loop.

        Args:
            approval_file: The approved APPROVAL_whatsapp_reply_*.md file.
            details: Dict with 'sender_name' and 'reply_message' keys.
        """
        sender = details["sender_name"]
        message = details["reply_message"]

        if not self._whatsapp_watcher:
            logger.error("WhatsApp watcher not available — cannot send reply to %s", sender)
            self._audit.log(LogEntry(
                action_type="whatsapp_reply_failed",
                source="approval_handler",
                status="failure",
                target_file=str(approval_file.relative_to(self.vault_path)),
                error="WhatsApp watcher not running",
            ))
            return

        # Capture file path for the callback closure
        done_dir = self._done
        audit = self._audit
        vault = self.vault_path

        def on_reply_sent(result: dict):
            """Callback executed after watcher sends the reply."""
            if result.get("status") == "sent":
                audit.log(LogEntry(
                    action_type="whatsapp_reply_sent",
                    source="approval_handler",
                    status="success",
                    target_file=str(approval_file.relative_to(vault)),
                    details={
                        "sender": sender,
                        "message_preview": message[:100],
                    },
                ))
                # Move approval file to Done/
                done_path = done_dir / approval_file.name
                if done_path.exists():
                    done_path = done_dir / f"{approval_file.stem}_{str(uuid.uuid4())[:8]}.md"
                if approval_file.exists():
                    approval_file.rename(done_path)
                    logger.info("WhatsApp reply sent to %s — approval moved to Done/", sender)
                update_dashboard(vault)
            else:
                error = result.get("error", "unknown")
                logger.error("Failed to send WhatsApp reply to %s: %s", sender, error)
                audit.log(LogEntry(
                    action_type="whatsapp_reply_failed",
                    source="approval_handler",
                    status="failure",
                    target_file=str(approval_file.relative_to(vault)),
                    error=error,
                ))

        self._whatsapp_watcher.queue_reply(
            sender_name=sender,
            message=message,
            callback=on_reply_sent,
        )
        logger.info("WhatsApp reply queued for %s — will send in next poll cycle", sender)

    @staticmethod
    def _parse_action_type(approval_file: Path) -> str:
        """Extract action_type from approval file frontmatter.

        Args:
            approval_file: Path to the APPROVAL_*.md file.

        Returns:
            Action type string or empty string if not found.
        """
        try:
            content = approval_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("action_type:"):
                    return stripped.split(":", 1)[1].strip()
                if stripped == "---" and "action_type" not in content[:content.index("---", 3)]:
                    break
        except (OSError, ValueError):
            pass
        return ""

    def _execute_gold_approval(self, approval_file: Path, action_type: str, domain: str) -> None:
        """Handle approved Gold tier actions (Facebook, Instagram, Odoo payment).

        These actions are executed by creating a processed action file that
        the orchestrator picks up and routes to the appropriate MCP server
        via the agent skill.

        Args:
            approval_file: The approved APPROVAL_*.md file.
            action_type: The type of action (facebook_post, instagram_reel, etc.).
            domain: The domain (facebook, instagram, odoo).
        """
        self._audit.log(LogEntry(
            action_type=f"{action_type}_approved",
            source="approval_handler",
            status="success",
            target_file=str(approval_file.relative_to(self.vault_path)),
            domain=domain,
        ))

        # Move approval file to Done/
        done_path = self._done / approval_file.name
        if done_path.exists():
            done_path = self._done / f"{approval_file.stem}_{str(uuid.uuid4())[:8]}.md"
        approval_file.rename(done_path)
        logger.info("%s approved — moved to Done/", action_type)

        update_dashboard(self.vault_path)
