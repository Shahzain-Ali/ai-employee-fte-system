"""LinkedIn Playwright Bot — Browser automation for posting, commenting, replying."""
import json
import os
import sys
import logging
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright, BrowserContext, Page
from playwright_stealth import Stealth

load_dotenv()

logger = logging.getLogger(__name__)

LINKEDIN_URL = "https://www.linkedin.com"
LOGIN_URL = "https://www.linkedin.com/login"
FEED_URL = "https://www.linkedin.com/feed/"

# Session persistence path
SESSION_PATH = Path(os.getenv("LINKEDIN_SESSION_PATH", ".sessions/linkedin"))


class LinkedInBot:
    """Playwright-based LinkedIn automation with session persistence.

    Uses persistent browser context so login is preserved across restarts.
    First run requires manual login; subsequent runs reuse the session.

    Async API — all methods are coroutines for MCP server compatibility.
    """

    def __init__(self, headless: bool = False, session_path: Path | None = None):
        self._session_path = session_path or SESSION_PATH
        self._headless = headless
        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def _clean_locks(self) -> None:
        """Remove stale lock files from previous crashed sessions."""
        for lock_file in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            lock_path = self._session_path / lock_file
            if lock_path.exists():
                lock_path.unlink(missing_ok=True)
                logger.debug("Removed stale lock: %s", lock_file)

    async def start(self) -> None:
        """Launch browser with persistent context and stealth."""
        self._session_path.mkdir(parents=True, exist_ok=True)
        self._clean_locks()

        self._playwright = await async_playwright().start()

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self._session_path),
            headless=self._headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        stealth = Stealth()
        await stealth.apply_stealth_async(self._context)

        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

        logger.info("LinkedIn bot browser started (headless=%s)", self._headless)

    async def stop(self) -> None:
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._context = None
        self._playwright = None
        logger.info("LinkedIn bot browser stopped")

    async def is_logged_in(self) -> bool:
        """Check if we're logged into LinkedIn by navigating and checking redirect."""
        try:
            current_url = self._page.url
            logger.info("Current URL: %s", current_url)

            # If already on feed, we're logged in
            if "/feed" in current_url:
                return True

            # Navigate to LinkedIn and check where it redirects
            await self._page.goto(LINKEDIN_URL, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
            current_url = self._page.url
            logger.info("After navigate URL: %s", current_url)

            if "/feed" in current_url or current_url.rstrip("/") == LINKEDIN_URL:
                return True

            if "/login" not in current_url and "/checkpoint" not in current_url:
                return True

            return False
        except Exception as e:
            logger.error("Login check failed: %s", e)
            return False

    async def login_interactive(self) -> bool:
        """Navigate to login page and wait for user to log in manually.

        Returns True when login is detected.
        """
        print("\n[LinkedIn Bot] Opening LinkedIn login page...")
        print("[LinkedIn Bot] Please log in manually in the browser window.")
        print("[LinkedIn Bot] Waiting for login to complete...\n")

        await self._page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)

        # Wait up to 5 minutes for user to complete login
        for i in range(300):
            await asyncio.sleep(1)
            current_url = self._page.url
            # After login, LinkedIn redirects away from /login
            if "/login" not in current_url and "/checkpoint" not in current_url and "linkedin.com" in current_url:
                await asyncio.sleep(3)
                print(f"[LinkedIn Bot] Detected redirect to: {current_url}")
                print("[LinkedIn Bot] Login successful!")
                logger.info("LinkedIn login completed successfully")
                return True
            if i % 30 == 0 and i > 0:
                print(f"[LinkedIn Bot] Still waiting... ({i}s, URL: {current_url})")

        print("[LinkedIn Bot] Login timeout (5 minutes). Please try again.")
        return False

    async def create_post(self, text: str) -> dict:
        """Create a new post on LinkedIn.

        Args:
            text: Post content.

        Returns:
            dict with status and details.
        """
        try:
            await self._page.goto(FEED_URL, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)

            # Click "Start a post" button (NOT the Video/Photo buttons below it)
            start_post_btn = None
            try:
                start_post_btn = await self._page.wait_for_selector(
                    'div.share-box-feed-entry__top-bar button', timeout=5000
                )
            except Exception:
                pass

            if not start_post_btn:
                return {"status": "error", "message": "Could not find 'Start a post' button"}

            await start_post_btn.click()
            await asyncio.sleep(2)

            # Find the ql-editor text area (LinkedIn uses Quill editor)
            editor = None
            editor_selectors = [
                'div.ql-editor[contenteditable="true"]',
                'div[role="textbox"][aria-label="Text editor for creating content"]',
                'div[data-placeholder="What do you want to talk about?"]',
                'div[role="textbox"][contenteditable="true"]',
            ]

            for sel in editor_selectors:
                try:
                    editor = await self._page.wait_for_selector(sel, timeout=5000)
                    if editor:
                        break
                except Exception:
                    continue

            if not editor:
                return {"status": "error", "message": "Could not find post editor"}

            # Type the post content
            await editor.click()
            await asyncio.sleep(0.5)

            # Handle multi-line text
            lines = text.split("\n")
            for i, line in enumerate(lines):
                await editor.type(line, delay=20)
                if i < len(lines) - 1:
                    await self._page.keyboard.press("Enter")
            await asyncio.sleep(1)

            # Click Post button inside the share modal
            post_btn = None
            post_selectors = [
                'button.share-actions__primary-action',
                'button[class*="share-actions__primary"]',
                'div.share-box button:has-text("Post")',
                'button:has-text("Post")',
            ]

            for sel in post_selectors:
                try:
                    post_btn = await self._page.wait_for_selector(sel, timeout=5000)
                    if post_btn and await post_btn.is_enabled():
                        break
                    post_btn = None
                except Exception:
                    continue

            if not post_btn:
                return {"status": "error", "message": "Could not find Post button"}

            await post_btn.click()
            await asyncio.sleep(3)

            logger.info("LinkedIn post created: %s", text[:50])
            return {"status": "success", "message": f"Post created: {text[:50]}..."}

        except Exception as e:
            logger.error("create_post failed: %s", e)
            return {"status": "error", "message": str(e)}

    async def comment_on_post(self, post_url: str, comment_text: str) -> dict:
        """Comment on a specific LinkedIn post.

        Args:
            post_url: Full URL of the LinkedIn post.
            comment_text: Comment content.

        Returns:
            dict with status and details.
        """
        try:
            await self._page.goto(post_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)

            # Click the comment button to open comment box
            comment_btn = await self._page.query_selector('button[aria-label*="Comment"]')
            if comment_btn:
                await comment_btn.click()
                await asyncio.sleep(2)

            # Find comment input
            comment_box = None
            comment_selectors = [
                'div.ql-editor[contenteditable="true"]',
                'div[role="textbox"][contenteditable="true"]',
                'div.comments-comment-box__form div[contenteditable="true"]',
            ]

            for sel in comment_selectors:
                try:
                    # Get the last matching element (comment box, not post editor)
                    elements = await self._page.query_selector_all(sel)
                    if elements:
                        comment_box = elements[-1]
                        break
                except Exception:
                    continue

            if not comment_box:
                return {"status": "error", "message": "Could not find comment box"}

            await comment_box.click()
            await asyncio.sleep(0.5)
            await comment_box.type(comment_text, delay=20)
            await asyncio.sleep(1)

            # Click submit comment button
            submit_btn = None
            submit_selectors = [
                'button.comments-comment-box__submit-button',
                'button[class*="comments-comment-box__submit"]',
                'button:has-text("Post")',
            ]

            for sel in submit_selectors:
                try:
                    elements = await self._page.query_selector_all(sel)
                    if elements:
                        submit_btn = elements[-1]
                        break
                except Exception:
                    continue

            if not submit_btn:
                return {"status": "error", "message": "Could not find submit button"}

            await submit_btn.click()
            await asyncio.sleep(3)

            logger.info("Comment posted on %s", post_url)
            return {"status": "success", "message": f"Comment posted on {post_url}"}

        except Exception as e:
            logger.error("comment_on_post failed: %s", e)
            return {"status": "error", "message": str(e)}

    async def like_post(self, post_url: str) -> dict:
        """Like a specific LinkedIn post.

        Args:
            post_url: Full URL of the LinkedIn post.

        Returns:
            dict with status and details.
        """
        try:
            await self._page.goto(post_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)

            like_btn = await self._page.query_selector('button[aria-label*="Like"]')
            if not like_btn:
                return {"status": "error", "message": "Could not find like button"}

            # Check if already liked
            aria_pressed = await like_btn.get_attribute("aria-pressed")
            if aria_pressed == "true":
                return {"status": "success", "message": "Post already liked"}

            await like_btn.click()
            await asyncio.sleep(1)

            logger.info("Post liked: %s", post_url)
            return {"status": "success", "message": f"Post liked: {post_url}"}

        except Exception as e:
            logger.error("like_post failed: %s", e)
            return {"status": "error", "message": str(e)}

    async def get_my_posts(self, limit: int = 10) -> dict:
        """Get recent posts from the logged-in user's profile activity.

        Args:
            limit: Maximum number of posts to return.

        Returns:
            dict with status and posts list.
        """
        try:
            # Navigate to user's recent activity
            await self._page.goto(FEED_URL, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)

            # Click on "Me" icon and go to profile
            me_btn = await self._page.query_selector('img.global-nav__me-photo')
            if me_btn:
                await me_btn.click()
                await asyncio.sleep(1)
                view_profile = await self._page.query_selector('a[href*="/in/"]')
                if view_profile:
                    await view_profile.click()
                    await asyncio.sleep(3)

            # Navigate to activity page
            activity_link = await self._page.query_selector('a[href*="/recent-activity/"]')
            if activity_link:
                await activity_link.click()
                await asyncio.sleep(3)

            posts = []
            post_elements = await self._page.query_selector_all('div.feed-shared-update-v2')

            for el in post_elements[:limit]:
                try:
                    text_el = await el.query_selector('span.break-words')
                    text = await text_el.inner_text() if text_el else ""

                    time_el = await el.query_selector('time')
                    timestamp = await time_el.get_attribute("datetime") if time_el else ""

                    link_el = await el.query_selector('a[href*="/feed/update/"]')
                    url = await link_el.get_attribute("href") if link_el else ""
                    if url and not url.startswith("http"):
                        url = f"https://www.linkedin.com{url}"

                    posts.append({
                        "text": text[:500],
                        "timestamp": timestamp,
                        "url": url,
                    })
                except Exception:
                    continue

            return {"status": "success", "posts": posts, "count": len(posts)}

        except Exception as e:
            logger.error("get_my_posts failed: %s", e)
            return {"status": "error", "message": str(e)}


# --- Standalone CLI for testing ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [linkedin-bot] %(message)s")

    async def main():
        bot = LinkedInBot(headless=False)
        await bot.start()

        try:
            if not await bot.is_logged_in():
                print("Not logged in. Starting interactive login...")
                if not await bot.login_interactive():
                    print("Login failed. Exiting.")
                    sys.exit(1)
            else:
                print("Already logged in!")

            if len(sys.argv) > 1:
                action = sys.argv[1]
                if action == "post" and len(sys.argv) > 2:
                    result = await bot.create_post(" ".join(sys.argv[2:]))
                    print(json.dumps(result, indent=2))
                elif action == "comment" and len(sys.argv) > 3:
                    result = await bot.comment_on_post(sys.argv[2], " ".join(sys.argv[3:]))
                    print(json.dumps(result, indent=2))
                elif action == "like" and len(sys.argv) > 2:
                    result = await bot.like_post(sys.argv[2])
                    print(json.dumps(result, indent=2))
                elif action == "posts":
                    result = await bot.get_my_posts()
                    print(json.dumps(result, indent=2))
                elif action == "login":
                    print("Login mode — session saved.")
                else:
                    print("Usage: python linkedin_bot.py [post <text>|comment <url> <text>|like <url>|posts|login]")
            else:
                print("Logged in. Use: post <text>, comment <url> <text>, like <url>, posts, login")
        finally:
            await bot.stop()

    asyncio.run(main())
