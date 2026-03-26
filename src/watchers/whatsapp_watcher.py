"""WhatsApp Watcher — monitors WhatsApp Web for keyword messages via Playwright."""
import json
import os
import queue
import re
import sys
import logging
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth

from src.watchers.base_watcher import BaseWatcher
from src.utils.logger import AuditLogger, LogEntry

logger = logging.getLogger(__name__)

WHATSAPP_URL = "https://web.whatsapp.com"


class WhatsAppWatcher(BaseWatcher):
    """Watches WhatsApp Web for unread messages containing configured keywords.

    Uses Playwright with launch_persistent_context for session persistence
    across restarts — no QR code re-scan needed after initial setup.
    Creates WA_{sender}_{timestamp}.md action files in Needs_Action/.
    """

    def __init__(
        self,
        vault_path: Path,
        session_path: str | None = None,
        keywords_path: str | None = None,
    ):
        super().__init__(vault_path)
        self._session_path = Path(
            session_path or os.getenv("WHATSAPP_SESSION_PATH", ".sessions/whatsapp")
        )
        self._keywords_path = Path(
            keywords_path or os.getenv("WHATSAPP_KEYWORDS_PATH", "config/keywords.json")
        )
        self._poll_interval = int(os.getenv("WHATSAPP_POLL_INTERVAL", "30"))
        self._headless = os.getenv("WHATSAPP_HEADLESS", "false").lower() == "true"
        self._running = False
        self._audit = AuditLogger(vault_path=vault_path)
        self._needs_action = self.vault_path / "Needs_Action"
        self._keywords = self._load_keywords()
        self._state_file = Path(".state/whatsapp_processed.json")
        self._processed_messages: set[str] = self._load_processed()

        # Playwright objects
        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

        # Thread-safe reply queue — approval handler puts replies here,
        # watcher processes them in its own thread (Playwright requirement)
        self._reply_queue: queue.Queue = queue.Queue()

    def _load_keywords(self) -> list[str]:
        """Load keyword list from config/keywords.json."""
        if self._keywords_path.exists():
            try:
                data = json.loads(self._keywords_path.read_text(encoding="utf-8"))
                keywords = data.get("whatsapp", [])
                logger.info("Loaded %d WhatsApp keywords", len(keywords))
                return [k.lower() for k in keywords]
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to load keywords: %s — using defaults", e)

        defaults = ["urgent", "asap", "invoice", "payment", "help"]
        logger.info("Using default keywords: %s", defaults)
        return defaults

    def _load_processed(self) -> set[str]:
        """Load previously processed message IDs from state file."""
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                ids = set(data.get("processed", []))
                logger.debug("Loaded %d processed message IDs", len(ids))
                return ids
            except (json.JSONDecodeError, KeyError):
                pass
        return set()

    def _save_processed(self) -> None:
        """Save processed message IDs to state file."""
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        # Keep only last 500 IDs to prevent file growing forever
        recent = list(self._processed_messages)[-500:]
        self._state_file.write_text(
            json.dumps({"processed": recent}, indent=2),
            encoding="utf-8",
        )

    def _launch_browser(self) -> None:
        """Launch Playwright browser with persistent context for session reuse."""
        self._session_path.mkdir(parents=True, exist_ok=True)

        # Clean stale lock files from previous crashed sessions
        for lock_file in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            lock_path = self._session_path / lock_file
            if lock_path.exists():
                lock_path.unlink(missing_ok=True)
                logger.debug("Removed stale lock: %s", lock_file)

        self._playwright = sync_playwright().start()

        # Use real Chrome user-agent to prevent WhatsApp blocking headless browsers
        chrome_ua = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self._session_path),
            headless=self._headless,
            user_agent=chrome_ua,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        stealth = Stealth()
        stealth.apply_stealth_sync(self._context)

        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()

        logger.info("Playwright browser launched (headless=%s)", self._headless)

    def _navigate_to_whatsapp(self) -> None:
        """Navigate to WhatsApp Web and wait for chat list to fully load."""
        self._page.goto(WHATSAPP_URL, wait_until="domcontentloaded", timeout=60000)
        # Wait for chat list to appear
        try:
            self._page.wait_for_selector(
                '[aria-label="Chat list"]', timeout=30000
            )
        except Exception:
            pass
        # Extra wait for unread badges to fully render
        time.sleep(5)
        logger.info("Navigated to WhatsApp Web")

    def _is_logged_in(self) -> bool:
        """Check if WhatsApp Web session is active (not showing QR code)."""
        try:
            self._page.wait_for_selector(
                '[aria-label="Chat list"], [data-ref], canvas[aria-label="Scan this QR code to link a device!"]',
                timeout=15000,
            )
            chat_list = self._page.query_selector('[aria-label="Chat list"]')
            return chat_list is not None
        except Exception:
            return False

    def _wait_for_qr_scan(self) -> bool:
        """Wait for user to scan QR code. Returns True if login succeeded."""
        logger.info("QR code detected — please scan with your phone")
        print("\n╔══════════════════════════════════════════╗")
        print("║  Scan the QR code with WhatsApp on your  ║")
        print("║  phone to link this device.               ║")
        print("║  Waiting up to 5 minutes...                ║")
        print("╚══════════════════════════════════════════╝\n")

        try:
            self._page.wait_for_selector(
                '[aria-label="Chat list"]',
                timeout=300000,
            )
            logger.info("WhatsApp Web login successful")
            print("WhatsApp Web connected successfully!")
            return True
        except Exception:
            logger.error("QR scan timeout — WhatsApp login failed")
            print("QR scan timed out. Please try again.")
            return False

    def start(self) -> None:
        """Start the WhatsApp watcher polling loop."""
        self._launch_browser()
        self._navigate_to_whatsapp()

        if not self._is_logged_in():
            if not self._wait_for_qr_scan():
                self._create_session_expired_notification()
                self._cleanup()
                return

        self._running = True
        logger.info(
            "WhatsApp Watcher started (keywords=%s, interval=%ds)",
            self._keywords,
            self._poll_interval,
        )

        while self._running:
            try:
                self.check_for_updates()
            except Exception as e:
                logger.error("WhatsApp check failed: %s", e)
                if not self._is_logged_in():
                    logger.error("WhatsApp session expired")
                    self._create_session_expired_notification()
                    self._running = False
                    break

            # Process any queued replies (from approval handler)
            self._process_reply_queue()

            # Process file-based queue (from MCP WhatsApp server)
            self._process_file_queue()

            time.sleep(self._poll_interval)

        self._cleanup()

    def queue_reply(self, sender_name: str, message: str, callback=None) -> None:
        """Thread-safe: queue a reply to be sent from the watcher's own thread.

        Args:
            sender_name: Contact name to reply to.
            message: Reply text.
            callback: Optional callable(result_dict) called after send.
        """
        self._reply_queue.put({
            "sender_name": sender_name,
            "message": message,
            "callback": callback,
        })
        logger.info("Reply queued for %s", sender_name)

    def _process_file_queue(self) -> None:
        """Process file-based send requests from MCP WhatsApp server.

        MCP server writes JSON files to .state/whatsapp_queue/send_*.json.
        Watcher sends using its open browser and writes result back.
        """
        queue_dir = Path(".state/whatsapp_queue")
        if not queue_dir.exists():
            return

        for req_file in sorted(queue_dir.glob("send_*.json")):
            try:
                request = json.loads(req_file.read_text(encoding="utf-8"))
                if request.get("status") != "pending":
                    continue

                contact = request["contact_name"]
                message = request["message"]
                request_id = request["id"]

                logger.info("Processing queued WhatsApp send to '%s'", contact)
                result = self.send_reply(sender_name=contact, message=message)

                # Write result file for MCP server to pick up
                result_file = queue_dir / f"result_{request_id}.json"
                result_file.write_text(
                    json.dumps({"status": "sent", "sender": contact}, indent=2),
                    encoding="utf-8",
                )

                # Remove request file
                req_file.unlink(missing_ok=True)
                logger.info("Queued WhatsApp message sent to '%s'", contact)

            except Exception as e:
                logger.error("Failed to process queued send %s: %s", req_file.name, e)
                # Write failure result
                try:
                    request = json.loads(req_file.read_text(encoding="utf-8"))
                    request_id = request.get("id", "unknown")
                    result_file = queue_dir / f"result_{request_id}.json"
                    result_file.write_text(
                        json.dumps({"status": "failed", "error": str(e)}, indent=2),
                        encoding="utf-8",
                    )
                    req_file.unlink(missing_ok=True)
                except Exception:
                    pass

    def _process_reply_queue(self) -> None:
        """Process all pending replies from the queue (runs in watcher thread)."""
        while not self._reply_queue.empty():
            try:
                item = self._reply_queue.get_nowait()
                result = self.send_reply(
                    sender_name=item["sender_name"],
                    message=item["message"],
                )
                if item.get("callback"):
                    item["callback"](result)
            except queue.Empty:
                break
            except Exception as e:
                logger.error("Failed to send queued reply: %s", e)
                if item.get("callback"):
                    item["callback"]({"status": "failed", "error": str(e)})

    def send_reply(self, sender_name: str, message: str) -> dict:
        """Send a reply using the watcher's existing browser session.

        Searches for the contact, opens the chat, types and sends the message.

        Args:
            sender_name: Contact name to search in WhatsApp.
            message: Reply text to send.

        Returns:
            Dict with 'status' and 'sender' keys.
        """
        if not self._page:
            raise RuntimeError("WhatsApp browser not running")

        logger.info("Sending reply to %s via existing browser", sender_name)

        # Click search box and search for contact
        search_box = self._page.wait_for_selector(
            '[aria-label="Search or start a new chat"]',
            timeout=10000,
        )
        if not search_box:
            raise RuntimeError("Could not find WhatsApp search box")

        search_box.click()
        time.sleep(1)
        search_box.fill(sender_name)
        time.sleep(2)

        # Click on matching chat
        chat_result = self._page.query_selector(f'span[title="{sender_name}"]')
        if not chat_result:
            chat_result = self._page.query_selector(f'span[title*="{sender_name}"]')
        if not chat_result:
            raise RuntimeError(f"Contact '{sender_name}' not found")

        chat_result.click()
        time.sleep(2)
        logger.info("Opened chat with: %s", sender_name)

        # Type and send message — try multiple selectors
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
                msg_input = self._page.wait_for_selector(sel, timeout=5000)
                if msg_input:
                    break
            except Exception:
                continue

        if not msg_input:
            raise RuntimeError("Could not find message input box")

        msg_input.click()
        time.sleep(0.5)

        lines = message.strip().split("\n")
        for i, line in enumerate(lines):
            msg_input.type(line, delay=20)
            if i < len(lines) - 1:
                self._page.keyboard.down("Shift")
                self._page.keyboard.press("Enter")
                self._page.keyboard.up("Shift")

        time.sleep(0.5)
        self._page.keyboard.press("Enter")
        time.sleep(2)

        # Clear search to go back to chat list
        try:
            esc = self._page.query_selector('[aria-label="Cancel search"]')
            if esc:
                esc.click()
                time.sleep(1)
        except Exception:
            pass

        logger.info("Reply sent to %s", sender_name)
        return {"status": "sent", "sender": sender_name}

    def stop(self) -> None:
        """Stop the WhatsApp watcher."""
        self._running = False
        logger.info("WhatsApp Watcher stopping...")

    def _cleanup(self) -> None:
        """Close browser and Playwright."""
        try:
            if self._context:
                self._context.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            logger.warning("Cleanup error: %s", e)

    def check_for_updates(self) -> list[Path]:
        """Check WhatsApp Web for unread messages with keywords.

        Flow:
        1. Immediately capture all unread badge chats (before auto-read)
        2. Click into each unread chat (max 5 chats)
        3. Read max 5 recent messages per chat, match keywords
        4. Create ONE action file per chat (all messages combined)

        Returns:
            List of created action file paths.
        """
        created_files = []

        # Step 1: Capture unread chats IMMEDIATELY (before badges disappear)
        try:
            unread_chats = self._capture_unread_chats(max_chats=5)
        except Exception as e:
            logger.error("Failed to capture unread chats: %s", e)
            return created_files

        if not unread_chats:
            logger.debug("No unread chats found")
            return created_files

        logger.info("Found %d unread chat(s) with badges", len(unread_chats))

        # Step 2: Click into each unread chat and read messages
        for chat_info in unread_chats:
            try:
                # Parse unread count from badge (e.g. "2 unread messages" → 2)
                unread_count = self._parse_unread_count(chat_info.get("badge", ""))
                # Cap at 5 messages max
                msg_limit = min(unread_count, 5) if unread_count > 0 else 5
                messages = self._get_messages_from_chat(chat_info, max_messages=msg_limit)

                # Collect all keyword-matched messages for this chat
                matched_messages = []
                all_keywords = set()

                for msg in messages:
                    matched_keywords = self._match_keywords(msg["text"])
                    if matched_keywords:
                        matched_messages.append(msg)
                        all_keywords.update(matched_keywords)

                if not matched_messages:
                    logger.debug("No keyword matches in chat: %s", chat_info["name"])
                    continue

                # Dedup: create a combined ID for all messages in this chat
                chat_dedup_id = self._chat_id(chat_info["name"], matched_messages)
                if chat_dedup_id in self._processed_messages:
                    continue

                # Create ONE action file per chat with all matched messages
                action_file = self._create_whatsapp_action_file(
                    sender_name=chat_info["name"],
                    chat_type=chat_info.get("type", "individual"),
                    group_name=chat_info.get("group_name", ""),
                    messages=matched_messages,
                    keywords_matched=sorted(all_keywords),
                )
                created_files.append(action_file)
                self._processed_messages.add(chat_dedup_id)

                if self.on_new_file:
                    self.on_new_file(action_file)

            except Exception as e:
                logger.error("Failed to process chat %s: %s", chat_info.get("name", "?"), e)

        # Persist processed message IDs to disk
        if created_files:
            self._save_processed()

        return created_files

    def _capture_unread_chats(self, max_chats: int = 5) -> list[dict]:
        """Scan ALL visible chats and capture ones with unread badges.

        This runs IMMEDIATELY after page load to grab badges before
        WhatsApp Web auto-reads them.

        Args:
            max_chats: Maximum number of unread chats to return.

        Returns:
            List of dicts with 'name', 'element', 'type' keys.
        """
        unread = []

        # Get all chat rows in the list
        chat_elements = self._page.query_selector_all(
            '[aria-label="Chat list"] [role="row"]'
        )

        if not chat_elements:
            chat_elements = self._page.query_selector_all(
                '[aria-label="Chat list"] div[tabindex="0"]'
            )

        logger.debug("Scanning %d chats for unread badges", len(chat_elements))

        for elem in chat_elements:
            if len(unread) >= max_chats:
                break

            try:
                # Check for unread badge (green circle with number)
                badge = elem.query_selector('span[aria-label*="unread"]')
                if not badge:
                    continue

                # Get chat name
                name_elem = elem.query_selector('span[title]')
                if not name_elem:
                    continue

                name = name_elem.get_attribute("title") or name_elem.inner_text()
                badge_text = badge.get_attribute("aria-label") or ""

                # Determine if group chat
                group_icon = elem.query_selector(
                    '[data-icon="default-group"], [data-icon="announcement-speaker"]'
                )
                chat_type = "group" if group_icon else "individual"

                unread.append({
                    "name": name,
                    "element": elem,
                    "type": chat_type,
                    "group_name": name if chat_type == "group" else "",
                    "badge": badge_text,
                })
                logger.info("Unread chat: %s (%s) — %s", name, chat_type, badge_text)

            except Exception as e:
                logger.debug("Error parsing chat element: %s", e)

        return unread

    def _get_messages_from_chat(self, chat_info: dict, max_messages: int = 5) -> list[dict]:
        """Click into a chat and extract recent incoming messages.

        Args:
            chat_info: Dict with 'name' and 'element' keys.
            max_messages: Maximum number of recent messages to read (default 5).

        Returns:
            List of message dicts with 'text', 'time', 'has_media' keys.
        """
        messages = []

        try:
            # Click on the chat to open it
            chat_info["element"].click()
            time.sleep(3)  # Wait for messages to load

            # WhatsApp Web uses div.message-in for incoming messages
            msg_elements = self._page.query_selector_all("div.message-in")

            if not msg_elements:
                logger.debug("No incoming messages found in %s", chat_info["name"])
                return messages

            # Get last N incoming messages only
            for msg_elem in msg_elements[-max_messages:]:
                try:
                    # Extract text from copyable-text div
                    text_elem = msg_elem.query_selector("div.copyable-text")
                    if not text_elem:
                        text_elem = msg_elem.query_selector("span.selectable-text")
                    if not text_elem:
                        continue

                    text = text_elem.inner_text().strip()
                    if not text:
                        continue

                    # Check for media
                    has_media = msg_elem.query_selector("img, video") is not None

                    # Get timestamp
                    msg_time = ""
                    pre_text = msg_elem.query_selector("[data-pre-plain-text]")
                    if pre_text:
                        msg_time = pre_text.get_attribute("data-pre-plain-text") or ""
                    if not msg_time:
                        time_span = msg_elem.query_selector("span[data-testid='msg-meta'] span, span.x1rg5ohu")
                        if time_span:
                            msg_time = time_span.inner_text()

                    messages.append({
                        "text": text,
                        "time": msg_time,
                        "has_media": has_media,
                    })
                except Exception as e:
                    logger.debug("Error parsing message: %s", e)

        except Exception as e:
            logger.error("Failed to read messages from %s: %s", chat_info["name"], e)

        return messages

    def _match_keywords(self, text: str) -> list[str]:
        """Check if message text contains any configured keywords."""
        text_lower = text.lower()
        return [kw for kw in self._keywords if kw in text_lower]

    @staticmethod
    def _parse_unread_count(badge_text: str) -> int:
        """Parse unread message count from badge aria-label.

        Examples: "2 unread messages" → 2, "1 unread message" → 1
        """
        match = re.search(r"(\d+)\s+unread", badge_text)
        if match:
            return int(match.group(1))
        return 0

    @staticmethod
    def _message_id(sender: str, text: str) -> str:
        """Generate a dedup ID for a message."""
        return f"{sender}:{text[:100]}"

    @staticmethod
    def _chat_id(sender: str, messages: list[dict]) -> str:
        """Generate a dedup ID for an entire chat's messages."""
        combined = "|".join(m["text"][:50] for m in messages)
        return f"{sender}:{combined}"

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize sender name for use in filename."""
        sanitized = re.sub(r"[^\w\-]", "_", name)
        return sanitized[:30].strip("_")

    def _create_whatsapp_action_file(
        self,
        sender_name: str,
        chat_type: str,
        group_name: str,
        messages: list[dict],
        keywords_matched: list[str],
    ) -> Path:
        """Create ONE WA_{sender}_{timestamp}.md action file per chat.

        All matched messages from the same chat are combined into a single file.
        """
        self._needs_action.mkdir(exist_ok=True)

        sanitized = self._sanitize_name(sender_name)
        now = datetime.now(timezone.utc)
        ts_compact = now.strftime("%Y%m%dT%H%M%SZ")
        entry_id = str(uuid.uuid4())
        iso_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        filename = f"WA_{sanitized}_{ts_compact}.md"
        action_path = self._needs_action / filename

        keywords_str = ", ".join(keywords_matched)
        keywords_yaml = ", ".join(f'"{k}"' for k in keywords_matched)
        msg_count = len(messages)
        has_media = any(m.get("has_media", False) for m in messages)

        # Build messages list for frontmatter (first message preview)
        first_msg = messages[0]["text"][:200] if messages else ""

        # Build message content section
        message_lines = []
        for i, msg in enumerate(messages, 1):
            time_str = msg.get("time", "")
            media_tag = " [has media]" if msg.get("has_media") else ""
            message_lines.append(f"{i}. [{time_str}] {msg['text']}{media_tag}")

        messages_content = "\n".join(message_lines)

        content = f"""---
id: {entry_id}
type: whatsapp
sender: {sender_name}
sender_name: {sender_name}
chat_type: {chat_type}
group_name: {group_name or "none"}
message_count: {msg_count}
message_preview: "{first_msg}"
detected_at: {iso_now}
keywords_matched: [{keywords_yaml}]
status: pending
has_media: {str(has_media).lower()}
skill: whatsapp_handler
---

# WhatsApp Messages: {sender_name}

**From**: {sender_name}
**Chat Type**: {chat_type}
**Group**: {group_name or "N/A"}
**Messages**: {msg_count} unread
**Keywords Matched**: {keywords_str}

## Messages

{messages_content}

## Suggested Actions

- [ ] Draft reply (considering all messages above)
- [ ] Forward to relevant contact
- [ ] Archive (no action needed)

## Processing

Use the `whatsapp_handler` skill as defined in `.claude/skills/whatsapp_handler.md`.

1. Read ALL messages above for full context
2. Analyze intent and urgency across all messages
3. Check Company_Handbook.md for handling rules
4. Draft ONE contextual reply addressing all messages
5. If reply needed: create approval request in Pending_Approval/
6. Update this file's status to `completed`
7. Move to `Done/`
8. Update `Dashboard.md`
9. Write log entry to `Logs/{now.strftime("%Y-%m-%d")}.json`
"""
        action_path.write_text(content, encoding="utf-8")

        self._audit.log(LogEntry(
            action_type="whatsapp_detected",
            source="whatsapp_watcher",
            status="success",
            target_file=f"Needs_Action/{filename}",
            details={
                "sender": sender_name,
                "chat_type": chat_type,
                "message_count": msg_count,
                "keywords_matched": keywords_matched,
                "platform": "whatsapp",
            },
        ))

        logger.info(
            "Created action file: %s (%d messages, keywords: %s)",
            filename, msg_count, keywords_str,
        )
        return action_path

    def _create_session_expired_notification(self) -> None:
        """Create a notification file when WhatsApp session expires."""
        notif_path = self.vault_path / "Needs_Action" / "SESSION_EXPIRED_whatsapp.md"
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        content = f"""---
type: notification
source: whatsapp_watcher
status: action_required
created_at: {now}
---

# WhatsApp Session Expired

The WhatsApp Web session has expired and requires re-authentication.

## Action Required

1. Run: `uv run python -m src.main whatsapp --setup`
2. Scan the QR code with your phone
3. Restart the system: `uv run python -m src.main run`

> This file was auto-created at {now}
"""
        notif_path.write_text(content, encoding="utf-8")
        logger.info("Session expired notification created")

        self._audit.log(LogEntry(
            action_type="session_expired",
            source="whatsapp_watcher",
            status="warning",
            details={"platform": "whatsapp"},
        ))


def _run_setup():
    """Run WhatsApp Web QR code setup — first-time login."""
    from dotenv import load_dotenv
    load_dotenv()

    vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))

    print("Starting WhatsApp Web setup...")
    print("A browser window will open. Scan the QR code with your phone.\n")

    watcher = WhatsAppWatcher(vault_path=vault_path)
    watcher._headless = False
    watcher._launch_browser()
    watcher._navigate_to_whatsapp()

    if watcher._is_logged_in():
        print("Already logged in to WhatsApp Web!")
        print("Session is saved. You can now run the watcher.")
    else:
        if watcher._wait_for_qr_scan():
            print("\nSetup complete! Session saved to:", watcher._session_path)
            print("You can now run: uv run python -m src.main run")
        else:
            print("\nSetup failed. Please try again.")

    watcher._cleanup()


def _run_once():
    """Run a single WhatsApp check and exit — for testing."""
    from dotenv import load_dotenv
    load_dotenv()

    vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
    watcher = WhatsAppWatcher(vault_path=vault_path)
    watcher._launch_browser()
    watcher._navigate_to_whatsapp()

    if not watcher._is_logged_in():
        print("Not logged in. Run 'python -m src.main whatsapp --setup' first.")
        watcher._cleanup()
        return

    print(f"Checking WhatsApp (keywords: {watcher._keywords})...")
    print(f"Previously processed: {len(watcher._processed_messages)} messages")
    files = watcher.check_for_updates()

    if files:
        print(f"Created {len(files)} action file(s):")
        for f in files:
            print(f"  → {f}")
    else:
        print("No new keyword messages found.")

    watcher._cleanup()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        _run_setup()
    elif len(sys.argv) > 1 and sys.argv[1] == "--once":
        _run_once()
    else:
        vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
        watcher = WhatsAppWatcher(vault_path=vault_path)
        try:
            watcher.start()
        except KeyboardInterrupt:
            watcher.stop()
