"""WhatsApp Sender — sends replies via Playwright after approval."""
import logging
import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

WHATSAPP_URL = "https://web.whatsapp.com"


def send_whatsapp_reply(
    sender_name: str,
    message: str,
    session_path: str | None = None,
) -> dict:
    """Send a WhatsApp reply via Playwright.

    Opens WhatsApp Web, searches for the contact, types the message, and sends it.

    Args:
        sender_name: The contact name to search for in WhatsApp.
        message: The reply message text to send.
        session_path: Path to persistent browser session. Defaults to WHATSAPP_SESSION_PATH env.

    Returns:
        Dict with 'status' and 'sender' keys.

    Raises:
        Exception: If browser launch, contact search, or message send fails.
    """
    session = Path(session_path or os.getenv("WHATSAPP_SESSION_PATH", ".sessions/whatsapp"))
    session.mkdir(parents=True, exist_ok=True)

    # Clean stale lock files
    for lock_file in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        lock_path = session / lock_file
        if lock_path.exists():
            lock_path.unlink(missing_ok=True)

    pw = sync_playwright().start()

    try:
        headless = os.getenv("WHATSAPP_HEADLESS", "false").lower() == "true"
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(session),
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        stealth = Stealth()
        stealth.apply_stealth_sync(context)

        page = context.pages[0] if context.pages else context.new_page()
        logger.info("Playwright browser launched for WhatsApp reply")

        # Navigate to WhatsApp Web
        page.goto(WHATSAPP_URL, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_selector('[aria-label="Chat list"]', timeout=30000)
        except Exception:
            pass
        time.sleep(5)
        logger.info("WhatsApp Web loaded")

        # Search for the contact
        search_box = page.wait_for_selector(
            '[aria-label="Search input textbox"]',
            timeout=10000,
        )
        if not search_box:
            raise RuntimeError("Could not find WhatsApp search box")

        search_box.click()
        time.sleep(1)
        search_box.fill(sender_name)
        time.sleep(2)

        # Click on the matching chat from search results
        chat_result = page.query_selector(f'span[title="{sender_name}"]')
        if not chat_result:
            # Try partial match
            chat_result = page.query_selector(f'span[title*="{sender_name}"]')
        if not chat_result:
            raise RuntimeError(f"Contact '{sender_name}' not found in WhatsApp")

        chat_result.click()
        time.sleep(2)
        logger.info("Opened chat with: %s", sender_name)

        # Type and send the message — try multiple selectors
        msg_input = None
        selectors = [
            'div[aria-label="Type a message"][contenteditable="true"]',
            'footer div[contenteditable="true"]',
            'div[title="Type a message"]',
            'div[data-tab="10"]',
            'p.selectable-text[contenteditable="true"]',
        ]
        for sel in selectors:
            try:
                msg_input = page.wait_for_selector(sel, timeout=5000)
                if msg_input:
                    logger.debug("Message input found with: %s", sel)
                    break
            except Exception:
                continue

        if not msg_input:
            raise RuntimeError("Could not find message input box")

        msg_input.click()
        time.sleep(0.5)

        # Type message line by line (Shift+Enter for newlines)
        lines = message.strip().split("\n")
        for i, line in enumerate(lines):
            msg_input.type(line, delay=20)
            if i < len(lines) - 1:
                page.keyboard.down("Shift")
                page.keyboard.press("Enter")
                page.keyboard.up("Shift")

        time.sleep(0.5)

        # Press Enter to send
        page.keyboard.press("Enter")
        time.sleep(2)
        logger.info("Reply sent to %s", sender_name)

        context.close()
        return {"status": "sent", "sender": sender_name}

    except Exception as e:
        logger.error("Failed to send WhatsApp reply to %s: %s", sender_name, e)
        raise
    finally:
        pw.stop()


def parse_approval_for_whatsapp(approval_file: Path) -> dict | None:
    """Parse an approval file to extract WhatsApp reply details.

    Args:
        approval_file: Path to the APPROVAL_whatsapp_reply_*.md file.

    Returns:
        Dict with 'sender_name' and 'reply_message' keys, or None if not a WhatsApp approval.
    """
    content = approval_file.read_text(encoding="utf-8")

    if "action_type: whatsapp_reply" not in content:
        return None

    details = {}
    lines = content.splitlines()
    in_frontmatter = False
    in_details = False
    current_key = None
    reply_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped == "---":
            if in_frontmatter:
                if reply_lines:
                    details["reply_message"] = "\n".join(reply_lines).strip()
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

        if stripped.startswith("sender_name:"):
            if current_key == "reply_message" and reply_lines:
                details["reply_message"] = "\n".join(reply_lines).strip()
                reply_lines = []
            details["sender_name"] = stripped.split(":", 1)[1].strip()
            current_key = "sender_name"
        elif stripped.startswith("reply_message:"):
            current_key = "reply_message"
            first_line = stripped.split(":", 1)[1].strip()
            reply_lines = [first_line] if first_line else []
        elif current_key == "reply_message":
            reply_lines.append(line.rstrip())

    if current_key == "reply_message" and reply_lines and "reply_message" not in details:
        details["reply_message"] = "\n".join(reply_lines).strip()

    # Also try parsing reply from body section (user writes in "Your Reply" section)
    if "reply_message" not in details or not details.get("reply_message"):
        reply_msg = _parse_reply_from_body(content)
        if reply_msg:
            details["reply_message"] = reply_msg

    # Also try parsing sender_name from frontmatter if not in details
    if "sender_name" not in details:
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("sender_name:") and "details" not in stripped:
                details["sender_name"] = stripped.split(":", 1)[1].strip()
                break

    if all(k in details for k in ("sender_name", "reply_message")) and details["reply_message"]:
        return details

    logger.warning("Could not parse WhatsApp reply details from %s", approval_file.name)
    return None


def _parse_reply_from_body(content: str) -> str | None:
    """Parse the user's reply from the 'Your Reply' section of the approval file.

    Looks for text after '## Your Reply' heading until the next '##' heading.
    Skips the '> Write your reply below this line:' marker if present.
    """
    lines = content.splitlines()
    in_reply = False
    reply_lines = []

    for line in lines:
        stripped = line.strip()

        # Start capturing after "## Your Reply" heading
        if stripped == "## Your Reply":
            in_reply = True
            continue

        if in_reply:
            # Stop at next heading
            if stripped.startswith("##"):
                break
            # Skip the instruction marker if user kept it
            if "> Write your reply below this line:" in line:
                continue
            reply_lines.append(line.rstrip())

    reply = "\n".join(reply_lines).strip()
    return reply if reply else None
