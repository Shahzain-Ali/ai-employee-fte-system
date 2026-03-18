"""Email Sender — sends emails via Gmail API after approval."""
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from googleapiclient.discovery import build

from src.watchers.gmail_auth import get_gmail_credentials

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str, html: bool = False,
               attachment: bytes = None, attachment_name: str = None) -> dict:
    """Send an email via Gmail API with optional attachment.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain text or HTML email body.
        html: If True, send body as HTML.
        attachment: Optional file bytes to attach.
        attachment_name: Filename for the attachment.

    Returns:
        Gmail API send response dict (contains 'id', 'threadId', 'labelIds').
    """
    creds = get_gmail_credentials()
    service = build("gmail", "v1", credentials=creds)

    if attachment and attachment_name:
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject

        subtype = "html" if html else "plain"
        message.attach(MIMEText(body, subtype))

        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={attachment_name}")
        message.attach(part)
    else:
        subtype = "html" if html else "plain"
        message = MIMEText(body, subtype)
        message["to"] = to
        message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    result = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )

    logger.info("Email sent to %s (id: %s)", to, result.get("id"))
    return result


def parse_approval_for_email(approval_file: Path) -> dict | None:
    """Parse an approval file to extract email reply details.

    Parses the YAML frontmatter 'details' block for to/subject/body.
    Body can be multi-line — all continuation lines (until next key or
    end of frontmatter) are collected.

    Args:
        approval_file: Path to the APPROVAL_email_send_*.md file.

    Returns:
        Dict with 'to', 'subject', 'body' keys, or None if not an email approval.
    """
    content = approval_file.read_text(encoding="utf-8")

    # Check this is an email_send approval
    if "action_type: email_send" not in content:
        return None

    # Parse from YAML frontmatter details block
    lines = content.splitlines()
    details = {}
    in_frontmatter = False
    in_details = False
    current_key = None
    body_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped == "---":
            if in_frontmatter:
                # End of frontmatter — flush body
                if body_lines:
                    details["body"] = "\n".join(body_lines).strip()
                break
            in_frontmatter = True
            continue

        if not in_frontmatter:
            continue

        if stripped == "details:":
            in_details = True
            continue

        if not in_details:
            continue

        # Inside details block — check for known keys
        if stripped.startswith("to:"):
            if current_key == "body" and body_lines:
                details["body"] = "\n".join(body_lines).strip()
                body_lines = []
            details["to"] = stripped.split(":", 1)[1].strip()
            current_key = "to"
        elif stripped.startswith("subject:"):
            if current_key == "body" and body_lines:
                details["body"] = "\n".join(body_lines).strip()
                body_lines = []
            details["subject"] = stripped.split(":", 1)[1].strip()
            current_key = "subject"
        elif stripped.startswith("body:"):
            current_key = "body"
            first_line = stripped.split(":", 1)[1].strip()
            body_lines = [first_line] if first_line else []
        elif current_key == "body":
            # Continuation line of multi-line body
            body_lines.append(line.rstrip())

    # Flush body if frontmatter ended without second ---
    if current_key == "body" and body_lines and "body" not in details:
        details["body"] = "\n".join(body_lines).strip()

    if all(k in details for k in ("to", "subject", "body")):
        return details

    logger.warning("Could not parse email details from %s", approval_file.name)
    return None
