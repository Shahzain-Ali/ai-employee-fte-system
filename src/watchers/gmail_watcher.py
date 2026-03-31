"""Gmail Watcher — monitors Gmail for unread important emails and creates action files."""
import os
import sys
import logging
import time
import base64
import uuid
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parseaddr

from googleapiclient.discovery import build

from src.watchers.base_watcher import BaseWatcher
from src.watchers.gmail_auth import get_gmail_credentials
from src.utils.logger import AuditLogger, LogEntry

logger = logging.getLogger(__name__)

# Sender patterns to skip — automated/noreply emails that never need action
SKIP_SENDER_PATTERNS: list[str] = [
    "noreply",
    "no-reply",
    "no_reply",
    "donotreply",
    "do-not-reply",
    "do_not_reply",
    "notification@",
    "notifications@",
    "alert@",
    "alerts@",
    "security@",
    "service@",
    "support@",
    "newsletter@",
    "news@",
    "digest@",
    "mailer-daemon@",
    "postmaster@",
    "statement@",
    "e.statement@",
    "online@",
    "hello@news.",
    "hello@info.",
    "hello@notify.",
    "hello@mail.",
    "promo",
    "marketing@",
    "updates@",
    "info@mail.",
    "info@email.",
    "team@mail.",
    "team@email.",
    "team@m.",
    "changelog@",
    "community@",
    "verify@",
    "invoice+",
    "topcompanies@",
    "jobs-listings@",
    "jobs@",
    "compliance@",
    "education-support@",
    "product@email.",
    "thehubspotteam@",
    "hello@eraser.io",
    "hello@sanity.io",
    "ship@info.",
    "email@email.",
    "notify@",
]

# Domains to always skip — newsletters, automated services
SKIP_DOMAINS: set[str] = {
    "substack.com",
    "beehiiv.com",
    "mail.beehiiv.com",
    "quora.com",
    "rumble.com",
    "ollama.com",
    "facebookmail.com",
    "mail.instagram.com",
    "telenorbank.pk",
    "nayapay.com",
    "skool.com",
    "news.railway.app",
    "email.claude.com",
    "promo1.bitget.com",
    "naukrigulf.com",
    "mail.anthropic.com",
    "neon.tech",
    "mail.replit.com",
    "x.com",
    "updates.resend.com",
    "qdrant.io",
    "linkedin.com",
    "em.linkedin.com",
    "indeed.com",
    "algorand.foundation",
    "faysalbank.com",
    "smailer1.binance.com",
    "binance.com",
    "email.sadapay.pk",
    "sadapay.pk",
    "surveylama.com",
    "notify.railway.app",
    "try.anaconda.com",
    "info.n8n.io",
    "m.ngrok.com",
    "t.upwork.com",
    "peopleperhour.com",
    "piaic.org",
    "eraser.io",
    "sanity.io",
    "info.vercel.com",
    "huggingface.co",
    "email.shopify.com",
    "auctane.com",
    "stackblitz.com",
}

# Specific senders to always skip
SKIP_SENDERS: set[str] = {
    "noreply@github.com",
    "support@github.com",
    "noreply@medium.com",
    "noreply@youtube.com",
    "noreply@google.com",
    "online@odoo.com",
    "superteampak@gmail.com",
    "google-cloud-compliance@google.com",
    "ericsimons@stackblitz.com",
    "steve@clerk.com",
    "systems@clerk.com",
    "braden@clerk.com",
}


def _is_skip_sender(email_addr: str) -> bool:
    """Check if sender should be skipped (noreply, automated, promotional)."""
    addr = email_addr.lower().strip()

    # Exact sender match
    if addr in SKIP_SENDERS:
        return True

    # Pattern match (substring in address)
    if any(pattern in addr for pattern in SKIP_SENDER_PATTERNS):
        return True

    # Domain match (everything after @)
    domain = addr.split("@", 1)[1] if "@" in addr else ""
    if domain in SKIP_DOMAINS:
        return True

    return False


class GmailWatcher(BaseWatcher):
    """Watches Gmail for unread important emails and creates EMAIL_*.md action files.

    Uses Google OAuth2 credentials to authenticate with Gmail API.
    Polls for emails matching a configurable query (default: 'is:unread is:important').
    Creates EMAIL_{message_id}.md in Needs_Action/ for each detected email.
    """

    def __init__(
        self,
        vault_path: Path,
        credentials_path: str | None = None,
        token_path: str | None = None,
    ):
        super().__init__(vault_path)
        self._credentials_path = credentials_path or os.getenv("GMAIL_CREDENTIALS_PATH")
        self._token_path = token_path or os.getenv("GMAIL_TOKEN_PATH")
        self._query = os.getenv(
            "GMAIL_QUERY",
            "is:unread category:primary",
        )
        self._poll_interval = int(os.getenv("POLL_INTERVAL", "120"))
        self._service = None
        self._running = False
        self._audit = AuditLogger(vault_path=vault_path)
        self._needs_action = self.vault_path / "Needs_Action"

    def _build_service(self):
        """Initialize Gmail API service."""
        creds = get_gmail_credentials(self._credentials_path, self._token_path)
        self._service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API service initialized")

    def start(self) -> None:
        """Start polling Gmail for new emails."""
        self._build_service()
        self._running = True
        logger.info(
            "Gmail Watcher started (query=%s, interval=%ds)",
            self._query,
            self._poll_interval,
        )

        while self._running:
            try:
                self.check_for_updates()
            except Exception as e:
                logger.error("Gmail check failed: %s", e)
                self._audit.log(LogEntry(
                    action_type="email_check_failed",
                    source="gmail_watcher",
                    status="failure",
                    error=str(e),
                ))
            time.sleep(self._poll_interval)

    def stop(self) -> None:
        """Stop the Gmail watcher."""
        self._running = False
        logger.info("Gmail Watcher stopped")

    def check_for_updates(self) -> list[Path]:
        """Check Gmail for unread important emails and create action files.

        Returns:
            List of created action file paths.
        """
        if not self._service:
            self._build_service()

        created_files = []

        try:
            results = (
                self._service.users()
                .messages()
                .list(userId="me", q=self._query, maxResults=5)
                .execute()
            )
        except Exception as e:
            logger.error("Gmail API list failed: %s", e)
            raise

        messages = results.get("messages", [])

        if not messages:
            logger.debug("No new emails matching query: %s", self._query)
            return created_files

        logger.info("Found %d emails matching query", len(messages))

        for msg_info in messages:
            msg_id = msg_info["id"]

            # Skip if already processed
            action_path = self._needs_action / f"EMAIL_{msg_id}.md"
            if action_path.exists():
                continue
            if (self.vault_path / "Done" / f"EMAIL_{msg_id}.md").exists():
                continue

            try:
                action_file = self._process_email(msg_id)
                if action_file:
                    created_files.append(action_file)

                    # Notify orchestrator
                    if self.on_new_file:
                        self.on_new_file(action_file)
            except Exception as e:
                logger.error("Failed to process email %s: %s", msg_id, e)

        return created_files

    def _process_email(self, message_id: str) -> Path | None:
        """Fetch email details and create action file.

        Args:
            message_id: Gmail message ID.

        Returns:
            Path to created action file, or None if skipped.
        """
        msg = (
            self._service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}

        from_raw = headers.get("from", "unknown")
        from_name, from_email = parseaddr(from_raw)

        # Skip noreply/automated senders
        if _is_skip_sender(from_email):
            logger.debug("Skipping automated sender: %s", from_email)
            # Mark as read so it doesn't keep appearing
            try:
                self._service.users().messages().modify(
                    userId="me", id=message_id,
                    body={"removeLabelIds": ["UNREAD"]},
                ).execute()
            except Exception:
                pass
            return None

        to_raw = headers.get("to", "unknown")
        subject = headers.get("subject", "(no subject)")
        date = headers.get("date", "")
        thread_id = msg.get("threadId", "")
        labels = msg.get("labelIds", [])
        snippet = msg.get("snippet", "")

        # Skip non-primary categories (Promotions, Social, Updates, Forums)
        SKIP_CATEGORIES = {"CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL", "CATEGORY_UPDATES", "CATEGORY_FORUMS"}
        if SKIP_CATEGORIES.intersection(labels):
            logger.debug("Skipping non-primary email: %s (labels: %s)", subject[:50], labels)
            try:
                self._service.users().messages().modify(
                    userId="me", id=message_id,
                    body={"removeLabelIds": ["UNREAD"]},
                ).execute()
            except Exception:
                pass
            return None

        # Extract body text
        body = self._extract_body(msg["payload"])
        body_preview = body[:500] if body else snippet

        # Skip promotional emails — real people don't have "unsubscribe" in their emails
        if body and "unsubscribe" in body.lower():
            logger.debug("Skipping promotional email (has unsubscribe): %s", subject[:50])
            try:
                self._service.users().messages().modify(
                    userId="me", id=message_id,
                    body={"removeLabelIds": ["UNREAD"]},
                ).execute()
            except Exception:
                pass
            return None

        # Check for attachments
        attachments = self._extract_attachment_names(msg["payload"])

        # Create action file
        action_file = self._create_email_action_file(
            message_id=message_id,
            thread_id=thread_id,
            from_email=from_email,
            from_name=from_name or from_email,
            to=to_raw,
            subject=subject,
            date=date,
            labels=labels,
            snippet=snippet,
            body_preview=body_preview,
            attachments=attachments,
        )

        # Mark as read in Gmail
        try:
            self._service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
            logger.debug("Marked email %s as read", message_id)
        except Exception as e:
            logger.warning("Failed to mark email %s as read: %s", message_id, e)

        # Log
        self._audit.log(LogEntry(
            action_type="email_detected",
            source="gmail_watcher",
            status="success",
            target_file=f"Needs_Action/EMAIL_{message_id}.md",
            details={
                "from": from_email,
                "subject": subject,
                "platform": "email",
                "message_id": message_id,
            },
        ))

        logger.info("Created action file for email: %s — %s", from_email, subject)
        return action_file

    def _extract_body(self, payload: dict) -> str:
        """Extract plain text body from email payload."""
        if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            # Recurse for multipart
            if part.get("parts"):
                result = self._extract_body(part)
                if result:
                    return result

        return ""

    def _extract_attachment_names(self, payload: dict) -> list[str]:
        """Extract attachment filenames from email payload."""
        names = []
        parts = payload.get("parts", [])
        for part in parts:
            filename = part.get("filename", "")
            if filename:
                names.append(filename)
            if part.get("parts"):
                names.extend(self._extract_attachment_names(part))
        return names

    def _create_email_action_file(
        self,
        message_id: str,
        thread_id: str,
        from_email: str,
        from_name: str,
        to: str,
        subject: str,
        date: str,
        labels: list[str],
        snippet: str,
        body_preview: str,
        attachments: list[str],
    ) -> Path:
        """Create EMAIL_{id}.md action file in Needs_Action/."""
        self._needs_action.mkdir(exist_ok=True)
        action_path = self._needs_action / f"EMAIL_{message_id}.md"

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry_id = str(uuid.uuid4())
        has_attachments = len(attachments) > 0
        attachment_list = ", ".join(attachments) if attachments else "none"
        labels_str = ", ".join(labels) if labels else "none"

        content = f"""---
id: {entry_id}
type: email
message_id: {message_id}
thread_id: {thread_id}
from: {from_email}
from_name: {from_name}
to: {to}
subject: "{subject}"
date: {date}
labels: [{labels_str}]
status: pending
detected_at: {now}
has_attachments: {str(has_attachments).lower()}
attachment_names: [{attachment_list}]
skill: email_responder
---

# Email: {subject}

**From**: {from_name} <{from_email}>
**To**: {to}
**Date**: {date}
**Labels**: {labels_str}

## Content

{body_preview}

## Suggested Actions

- [ ] Draft reply
- [ ] Forward to relevant contact
- [ ] Archive (no action needed)

## Processing

Use the `email_responder` skill as defined in `.claude/skills/email_responder.md`.

1. Read this email content
2. Analyze intent and urgency
3. Check Company_Handbook.md for email handling rules
4. If reply needed: create approval request in Pending_Approval/
5. Update this file's status to `completed`
6. Move to `Done/`
7. Update `Dashboard.md`
8. Write log entry to `Logs/{datetime.now(timezone.utc).strftime("%Y-%m-%d")}.json`
"""
        action_path.write_text(content, encoding="utf-8")
        return action_path


def _run_authorize():
    """Run authorization flow only — for first-time setup."""
    print("Starting Gmail OAuth2 authorization...")
    print("A browser window will open. Grant access to your Gmail account.")
    creds = get_gmail_credentials()
    print(f"Authorization successful! Token saved.")
    print(f"Gmail watcher is ready to use.")


def _run_once():
    """Run a single check and exit — for testing."""
    from dotenv import load_dotenv
    load_dotenv()

    vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
    watcher = GmailWatcher(vault_path=vault_path)
    watcher._build_service()

    print(f"Checking Gmail (query: {watcher._query})...")
    files = watcher.check_for_updates()

    if files:
        print(f"Created {len(files)} action file(s):")
        for f in files:
            print(f"  → {f}")
    else:
        print("No new emails found.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if len(sys.argv) > 1 and sys.argv[1] == "--authorize":
        _run_authorize()
    elif len(sys.argv) > 1 and sys.argv[1] == "--once":
        _run_once()
    else:
        vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
        watcher = GmailWatcher(vault_path=vault_path)
        try:
            watcher.start()
        except KeyboardInterrupt:
            watcher.stop()
