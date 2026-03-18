"""Twitter/X Playwright Bot — Browser automation for tweet posting, replying, liking.

Uses Firefox headless with cookie injection from Chromium session.
Twitter/X blocks headless Chromium (blank page) but Firefox headless works.
Login is done once in Chromium (non-headless), cookies are exported,
then Firefox headless uses those cookies for all MCP operations.
"""
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

TWITTER_URL = "https://x.com"
LOGIN_URL = "https://x.com/i/flow/login"

# Session paths
CHROMIUM_SESSION_PATH = Path(os.getenv("TWITTER_SESSION_PATH", ".sessions/twitter"))
FIREFOX_SESSION_PATH = Path(os.getenv("TWITTER_FF_SESSION_PATH", ".sessions/twitter-ff2"))
COOKIES_PATH = Path(os.getenv("TWITTER_COOKIES_PATH", ".sessions/twitter_cookies.json"))


class TwitterBot:
    """Playwright-based Twitter/X automation with session persistence.

    MCP mode (headless=True): Uses Firefox + injected cookies.
    Login mode (headless=False): Uses Chromium for manual login + cookie export.

    Async API — all methods are coroutines for MCP server compatibility.
    """

    def __init__(self, headless: bool = False, session_path: Path | None = None):
        self._headless = headless
        self._chromium_session = session_path or CHROMIUM_SESSION_PATH
        self._firefox_session = FIREFOX_SESSION_PATH
        self._cookies_path = COOKIES_PATH
        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def _clean_locks(self, path: Path) -> None:
        """Remove stale lock files from previous crashed sessions."""
        # Chromium locks
        for lock_file in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            lock_path = path / lock_file
            if lock_path.exists():
                lock_path.unlink(missing_ok=True)
        # Firefox locks
        for lock_file in ("lock", "parent.lock", ".parentlock"):
            lock_path = path / lock_file
            if lock_path.exists():
                lock_path.unlink(missing_ok=True)

    async def start(self) -> None:
        """Launch browser — Firefox headless for MCP, Chromium for login."""
        self._playwright = await async_playwright().start()

        if self._headless:
            # MCP mode: Firefox headless with cookie injection
            self._firefox_session.mkdir(parents=True, exist_ok=True)
            self._clean_locks(self._firefox_session)

            self._context = await self._playwright.firefox.launch_persistent_context(
                user_data_dir=str(self._firefox_session),
                headless=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
            )
            stealth = Stealth()
            await stealth.apply_stealth_async(self._context)

            # Inject cookies from Chromium session
            if self._cookies_path.exists():
                await self._inject_cookies()
            else:
                logger.warning("No cookies file found at %s", self._cookies_path)
        else:
            # Login mode: Chromium non-headless
            self._chromium_session.mkdir(parents=True, exist_ok=True)
            self._clean_locks(self._chromium_session)

            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self._chromium_session),
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--no-first-run",
                ],
                ignore_default_args=["--enable-automation"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            )
            stealth = Stealth()
            await stealth.apply_stealth_async(self._context)

        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

        logger.info("Twitter bot started (headless=%s, browser=%s)",
                     self._headless, "firefox" if self._headless else "chromium")

    async def _inject_cookies(self) -> None:
        """Load cookies from JSON file and inject into browser context."""
        try:
            all_cookies = json.loads(self._cookies_path.read_text(encoding="utf-8"))
            x_cookies = []
            for c in all_cookies:
                domain = c.get("domain", "")
                if ".x.com" not in domain and "twitter" not in domain:
                    continue
                cookie = {
                    "name": c["name"],
                    "value": c["value"],
                    "domain": c["domain"],
                    "path": c.get("path", "/"),
                }
                if c.get("expires", -1) > 0:
                    cookie["expires"] = c["expires"]
                if c.get("secure"):
                    cookie["secure"] = True
                if c.get("httpOnly"):
                    cookie["httpOnly"] = True
                if c.get("sameSite"):
                    cookie["sameSite"] = c["sameSite"]
                x_cookies.append(cookie)

            if x_cookies:
                await self._context.add_cookies(x_cookies)
                logger.info("Injected %d Twitter cookies", len(x_cookies))
            else:
                logger.warning("No Twitter cookies found in %s", self._cookies_path)
        except Exception as e:
            logger.error("Failed to inject cookies: %s", e)

    async def _export_cookies(self) -> None:
        """Export all cookies from Chromium session to JSON file for Firefox reuse."""
        try:
            cookies = await self._context.cookies()
            self._cookies_path.parent.mkdir(parents=True, exist_ok=True)
            self._cookies_path.write_text(
                json.dumps(cookies, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            x_count = sum(1 for c in cookies
                          if ".x.com" in c.get("domain", "") or "twitter" in c.get("domain", ""))
            logger.info("Exported %d cookies (%d Twitter) to %s",
                        len(cookies), x_count, self._cookies_path)
        except Exception as e:
            logger.error("Failed to export cookies: %s", e)

    async def stop(self) -> None:
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._context = None
        self._playwright = None
        logger.info("Twitter bot browser stopped")

    async def is_logged_in(self) -> bool:
        """Check if we're logged into Twitter/X by navigating and checking for home feed."""
        try:
            # Navigate to x.com and see where it redirects
            await self._page.goto(TWITTER_URL, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(5)
            current_url = self._page.url
            logger.info("Login check URL: %s", current_url)

            # Logged-in users get redirected to /home
            if "/home" in current_url:
                return True

            # Check if page has "Sign in" text — means NOT logged in
            sign_in = await self._page.query_selector('a[href="/login"]')
            if sign_in:
                return False

            # Check for home timeline elements (logged-in indicator)
            timeline = await self._page.query_selector('div[data-testid="primaryColumn"]')
            if timeline:
                return True

            return False
        except Exception as e:
            logger.error("Login check failed: %s", e)
            return False

    async def login_interactive(self) -> bool:
        """Navigate to x.com and wait for user to log in manually (Chromium).

        After successful login, exports cookies for Firefox headless reuse.
        Returns True when login is detected.
        """
        print("\n[Twitter Bot] Opening x.com...")
        print("[Twitter Bot] Please log in manually in the browser window.")
        print("[Twitter Bot] Use your USERNAME (not email) + PASSWORD to login.")
        print("[Twitter Bot] Or use 'Sign in with Google' if direct login doesn't work.")
        print("[Twitter Bot] Waiting for login to complete...\n")

        # Go to x.com homepage instead of direct login URL (less suspicious)
        await self._page.goto(TWITTER_URL, wait_until="domcontentloaded", timeout=30000)

        # Wait up to 5 minutes for user to complete login
        for i in range(300):
            await asyncio.sleep(1)
            current_url = self._page.url
            # After login, Twitter redirects to /home
            if "/home" in current_url:
                await asyncio.sleep(3)
                print(f"[Twitter Bot] Detected redirect to: {current_url}")
                print("[Twitter Bot] Login successful!")
                logger.info("Twitter login completed successfully")

                # Export cookies for Firefox headless reuse
                await self._export_cookies()
                print("[Twitter Bot] Cookies exported for headless mode.")
                return True
            if i % 30 == 0 and i > 0:
                print(f"[Twitter Bot] Still waiting... ({i}s, URL: {current_url})")

        print("[Twitter Bot] Login timeout (5 minutes). Please try again.")
        return False

    async def _dismiss_overlays(self) -> None:
        """Dismiss cookie banners, notification prompts, and other popups."""
        dismiss_selectors = [
            'div[data-testid="BottomBar"] button',
            'button[data-testid="sheetCloseButton"]',
        ]
        for sel in dismiss_selectors:
            try:
                btn = await self._page.query_selector(sel)
                if btn and await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(0.5)
                    logger.debug("Dismissed overlay: %s", sel)
            except Exception:
                continue

    async def post_tweet(self, text: str) -> dict:
        """Post a new tweet/post on Twitter/X.

        Args:
            text: Tweet content (max 280 characters).

        Returns:
            dict with status and details.
        """
        try:
            # Go to home first to ensure we're logged in
            await self._page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
            await self._dismiss_overlays()

            # Navigate to compose page
            await self._page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)

            # Find the tweet compose box
            compose_box = None
            selectors = [
                'div[data-testid="tweetTextarea_0"]',
                'div[role="textbox"][data-testid="tweetTextarea_0"]',
                'div[contenteditable="true"][role="textbox"]',
            ]

            for sel in selectors:
                try:
                    compose_box = await self._page.wait_for_selector(sel, timeout=5000)
                    if compose_box:
                        break
                except Exception:
                    continue

            if not compose_box:
                return {"status": "error", "message": "Could not find tweet compose box"}

            # Click compose box and type
            await compose_box.click()
            await asyncio.sleep(0.5)
            await compose_box.type(text, delay=30)
            await asyncio.sleep(2)

            # Find Post button and wait for it to be enabled
            post_btn = await self._page.wait_for_selector(
                'button[data-testid="tweetButton"]', timeout=5000
            )

            if not post_btn:
                return {"status": "error", "message": "Could not find Post button"}

            # Wait for button to become enabled (it's disabled until text is typed)
            for _ in range(10):
                is_enabled = await post_btn.is_enabled()
                if is_enabled:
                    break
                await asyncio.sleep(0.5)

            # Use JavaScript click to avoid overlay interception
            await self._page.evaluate('document.querySelector(\'button[data-testid="tweetButton"]\').click()')
            await asyncio.sleep(4)

            # Verify we got redirected away from compose (tweet was sent)
            current_url = self._page.url
            if "/compose" not in current_url:
                logger.info("Tweet posted: %s", text[:50])
                return {"status": "success", "message": f"Tweet posted: {text[:50]}..."}
            else:
                return {"status": "error", "message": "Post button clicked but tweet may not have been sent"}

            logger.info("Tweet posted: %s", text[:50])
            return {"status": "success", "message": f"Tweet posted: {text[:50]}..."}

        except Exception as e:
            logger.error("post_tweet failed: %s", e)
            return {"status": "error", "message": str(e)}

    async def reply_to_tweet(self, tweet_url: str, reply_text: str) -> dict:
        """Reply to a specific tweet.

        Args:
            tweet_url: Full URL of the tweet to reply to.
            reply_text: Reply content.

        Returns:
            dict with status and details.
        """
        try:
            await self._page.goto(tweet_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
            await self._dismiss_overlays()

            # Find the reply box on the tweet page
            reply_box = None
            selectors = [
                'div[data-testid="tweetTextarea_0"]',
                'div[role="textbox"][data-testid="tweetTextarea_0"]',
                'div[contenteditable="true"][role="textbox"]',
            ]

            for sel in selectors:
                try:
                    reply_box = await self._page.wait_for_selector(sel, timeout=5000)
                    if reply_box:
                        break
                except Exception:
                    continue

            if not reply_box:
                return {"status": "error", "message": "Could not find reply box"}

            await reply_box.click()
            await asyncio.sleep(0.5)
            await reply_box.type(reply_text, delay=30)
            await asyncio.sleep(1)

            # Click Reply button
            reply_btn = None
            btn_selectors = [
                'button[data-testid="tweetButton"]',
                'button[data-testid="tweetButtonInline"]',
            ]

            for sel in btn_selectors:
                try:
                    reply_btn = await self._page.wait_for_selector(sel, timeout=3000)
                    if reply_btn:
                        break
                except Exception:
                    continue

            if not reply_btn:
                return {"status": "error", "message": "Could not find Reply button"}

            await reply_btn.click(force=True)
            await asyncio.sleep(3)

            logger.info("Reply posted to %s", tweet_url)
            return {"status": "success", "message": f"Reply posted to {tweet_url}"}

        except Exception as e:
            logger.error("reply_to_tweet failed: %s", e)
            return {"status": "error", "message": str(e)}

    async def like_tweet(self, tweet_url: str) -> dict:
        """Like a specific tweet.

        Args:
            tweet_url: Full URL of the tweet to like.

        Returns:
            dict with status and details.
        """
        try:
            await self._page.goto(tweet_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
            await self._dismiss_overlays()

            like_btn = await self._page.query_selector('button[data-testid="like"]')
            if not like_btn:
                # Check if already liked
                unlike_btn = await self._page.query_selector('button[data-testid="unlike"]')
                if unlike_btn:
                    return {"status": "success", "message": "Tweet already liked"}
                return {"status": "error", "message": "Could not find like button"}

            await like_btn.click(force=True)
            await asyncio.sleep(1)

            logger.info("Tweet liked: %s", tweet_url)
            return {"status": "success", "message": f"Tweet liked: {tweet_url}"}

        except Exception as e:
            logger.error("like_tweet failed: %s", e)
            return {"status": "error", "message": str(e)}

    async def get_my_tweets(self, limit: int = 10) -> dict:
        """Get recent tweets from the logged-in user's profile.

        Args:
            limit: Maximum number of tweets to return.

        Returns:
            dict with status and tweets list.
        """
        try:
            handle = os.getenv("TWITTER_HANDLE", "").lstrip("@")
            if not handle:
                return {"status": "error", "message": "TWITTER_HANDLE not set in .env"}

            await self._page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(5)
            await self._dismiss_overlays()

            tweets = []
            tweet_elements = await self._page.query_selector_all('article[data-testid="tweet"]')

            for el in tweet_elements[:limit]:
                try:
                    text_el = await el.query_selector('div[data-testid="tweetText"]')
                    text = await text_el.inner_text() if text_el else ""

                    time_el = await el.query_selector("time")
                    timestamp = await time_el.get_attribute("datetime") if time_el else ""

                    # Get tweet URL from the timestamp link
                    link_el = await el.query_selector('a[href*="/status/"]')
                    href = await link_el.get_attribute('href') if link_el else ""
                    url = f"https://x.com{href}" if href else ""

                    tweets.append({
                        "text": text[:280],
                        "timestamp": timestamp,
                        "url": url,
                    })
                except Exception:
                    continue

            return {"status": "success", "tweets": tweets, "count": len(tweets)}

        except Exception as e:
            logger.error("get_my_tweets failed: %s", e)
            return {"status": "error", "message": str(e)}


# --- Standalone CLI for testing ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [twitter-bot] %(message)s")

    async def main():
        bot = TwitterBot(headless=False)
        await bot.start()

        try:
            if not await bot.is_logged_in():
                print("Not logged in. Starting interactive login...")
                if not await bot.login_interactive():
                    print("Login failed. Exiting.")
                    sys.exit(1)
            else:
                print("Already logged in!")
                # Export cookies even if already logged in
                await bot._export_cookies()
                print("Cookies exported for headless mode.")

            if len(sys.argv) > 1:
                action = sys.argv[1]
                if action == "post" and len(sys.argv) > 2:
                    result = await bot.post_tweet(" ".join(sys.argv[2:]))
                    print(json.dumps(result, indent=2))
                elif action == "reply" and len(sys.argv) > 3:
                    result = await bot.reply_to_tweet(sys.argv[2], " ".join(sys.argv[3:]))
                    print(json.dumps(result, indent=2))
                elif action == "like" and len(sys.argv) > 2:
                    result = await bot.like_tweet(sys.argv[2])
                    print(json.dumps(result, indent=2))
                elif action == "tweets":
                    result = await bot.get_my_tweets()
                    print(json.dumps(result, indent=2))
                elif action == "login":
                    print("Login mode — session saved.")
                else:
                    print("Usage: python twitter_bot.py [post <text>|reply <url> <text>|like <url>|tweets|login]")
            else:
                print("Logged in. Use: post <text>, reply <url> <text>, like <url>, tweets, login")
        finally:
            await bot.stop()

    asyncio.run(main())
