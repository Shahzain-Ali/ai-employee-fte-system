"""MCP Server: fte-email — Send emails via Gmail API with optional attachments."""
import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Ensure project root is on sys.path so `src.*` imports work regardless of cwd
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [fte-email] %(message)s")
logger = logging.getLogger("fte-email")

mcp = FastMCP("fte-email")


@mcp.tool()
def send_email_tool(to: str, subject: str, body: str, attachment_path: str = "") -> str:
    """Send an email via Gmail API with optional PDF attachment.

    Args:
        to: Recipient email address (e.g. client@example.com).
        subject: Email subject line.
        body: Plain text email body content.
        attachment_path: Optional local file path to attach (e.g. invoice PDF).
    """
    try:
        from src.utils.email_sender import send_email

        attachment_bytes = None
        attachment_name = None
        if attachment_path:
            file_path = Path(attachment_path)
            if file_path.exists():
                attachment_bytes = file_path.read_bytes()
                attachment_name = file_path.name
                logger.info("Attaching file: %s (%d bytes)", attachment_name, len(attachment_bytes))
            else:
                logger.warning("Attachment not found: %s", attachment_path)

        result = send_email(
            to=to, subject=subject, body=body,
            attachment=attachment_bytes, attachment_name=attachment_name
        )
        msg_id = result.get("id", "unknown")
        attach_info = f" with attachment '{attachment_name}'" if attachment_name else ""
        return f"Email sent successfully to {to}{attach_info} (Gmail ID: {msg_id})"
    except Exception as e:
        logger.error("MCP send_email failed: %s", e)
        return f"Error sending email: {e}"


@mcp.tool()
def draft_email_tool(to: str, subject: str, body: str) -> str:
    """Preview an email without sending it. Returns the formatted email for review.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain text email body content.
    """
    return (
        f"--- EMAIL DRAFT (not sent) ---\n"
        f"To: {to}\n"
        f"Subject: {subject}\n"
        f"---\n"
        f"{body}\n"
        f"---\n"
        f"Use send_email_tool to actually send this email."
    )


if __name__ == "__main__":
    mcp.run()
