"""Twitter/X Playwright Bot — Browser automation for tweet posting, replying, liking."""
import json
import os
import sys
import logging
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, BrowserContext, Page
from playwright_stealth import Stealth

load_dotenv()

logger = logging.getLogger(__name__)

TWITTER_URL = "https://x.com"
LOGIN_URL = "https://x.com/i/flow/login"

# Session persistence path
SESSION_PATH = Path(os.getenv("TWITTER_SESSION_PATH", ".sessions/twitter"))


class TwitterBot:
    """Playwright-based Twitter/X automation with session persistence.

    Uses persistent browser context so login is preserved across restarts.
    First run requires manual login; subsequent runs reuse the session.
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

    def start(self) -> None:
        """Launch browser with persistent context and stealth."""
        self._session_path.mkdir(parents=True, exist_ok=True)
        self._clean_locks()

        self._playwright = sync_playwright().start()

        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self._session_path),
            headless=self._headless,
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
        stealth.apply_stealth_sync(self._context)

        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()

        logger.info("Twitter bot browser started (headless=%s)", self._headless)

    def stop(self) -> None:
        """Close browser and cleanup."""
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()
        self._page = None
        self._context = None
        self._playwright = None
        logger.info("Twitter bot browser stopped")

    def is_logged_in(self) -> bool:
        """Check if we're logged into Twitter/X."""
        try:
            current_url = self._page.url
            logger.info("Current URL: %s", current_url)

            # If URL has /home, we're logged in
            if "/home" in current_url:
                return True

            # Navigate to x.com and check redirect
            self._page.goto(TWITTER_URL, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
            current_url = self._page.url
            logger.info("After navigate URL: %s", current_url)

            if "/home" in current_url:
                return True

            # Check if login page is NOT showing
            if "/login" not in current_url and "/i/flow/login" not in current_url:
                nav = self._page.query_selector('nav') or self._page.query_selector('header')
                if nav:
                    return True

            return False
        except Exception as e:
            logger.error("Login check failed: %s", e)
            return False

    def login_interactive(self) -> bool:
        """Navigate to x.com and wait for user to log in manually.

        Returns True when login is detected.
        """
        print("\n[Twitter Bot] Opening x.com...")
        print("[Twitter Bot] Please log in manually in the browser window.")
        print("[Twitter Bot] Use your USERNAME (not email) + PASSWORD to login.")
        print("[Twitter Bot] DO NOT use 'Sign in with Google'.")
        print("[Twitter Bot] Waiting for login to complete...\n")

        # Go to x.com homepage instead of direct login URL (less suspicious)
        self._page.goto(TWITTER_URL, wait_until="domcontentloaded", timeout=30000)

        # Wait up to 5 minutes for user to complete login
        for i in range(300):
            time.sleep(1)
            current_url = self._page.url
            # After login, Twitter redirects to /home
            if "/home" in current_url:
                time.sleep(3)
                print(f"[Twitter Bot] Detected redirect to: {current_url}")
                print("[Twitter Bot] Login successful!")
                logger.info("Twitter login completed successfully")
                return True
            if i % 30 == 0 and i > 0:
                print(f"[Twitter Bot] Still waiting... ({i}s, URL: {current_url})")

        print("[Twitter Bot] Login timeout (5 minutes). Please try again.")
        return False

    def post_tweet(self, text: str) -> dict:
        """Post a new tweet/post on Twitter/X.

        Args:
            text: Tweet content (max 280 characters).

        Returns:
            dict with status and details.
        """
        try:
            self._page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)

            # Find the tweet compose box
            compose_box = None
            selectors = [
                'div[data-testid="tweetTextarea_0"]',
                'div[role="textbox"][data-testid="tweetTextarea_0"]',
                'div.DraftEditor-root',
                'div[contenteditable="true"][role="textbox"]',
            ]

            for sel in selectors:
                try:
                    compose_box = self._page.wait_for_selector(sel, timeout=5000)
                    if compose_box:
                        break
                except Exception:
                    continue

            if not compose_box:
                return {"status": "error", "message": "Could not find tweet compose box"}

            # Type the tweet text
            compose_box.click()
            time.sleep(0.5)
            compose_box.type(text, delay=30)
            time.sleep(1)

            # Click the Post button
            post_btn = None
            post_selectors = [
                'button[data-testid="tweetButton"]',
                'button[data-testid="tweetButtonInline"]',
                'div[data-testid="tweetButton"]',
            ]

            for sel in post_selectors:
                try:
                    post_btn = self._page.wait_for_selector(sel, timeout=3000)
                    if post_btn:
                        break
                except Exception:
                    continue

            if not post_btn:
                return {"status": "error", "message": "Could not find Post button"}

            post_btn.click()
            time.sleep(3)

            logger.info("Tweet posted: %s", text[:50])
            return {"status": "success", "message": f"Tweet posted: {text[:50]}..."}

        except Exception as e:
            logger.error("post_tweet failed: %s", e)
            return {"status": "error", "message": str(e)}

    def reply_to_tweet(self, tweet_url: str, reply_text: str) -> dict:
        """Reply to a specific tweet.

        Args:
            tweet_url: Full URL of the tweet to reply to.
            reply_text: Reply content.

        Returns:
            dict with status and details.
        """
        try:
            self._page.goto(tweet_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)

            # Find the reply box on the tweet page
            reply_box = None
            selectors = [
                'div[data-testid="tweetTextarea_0"]',
                'div[role="textbox"][data-testid="tweetTextarea_0"]',
                'div[contenteditable="true"][role="textbox"]',
            ]

            for sel in selectors:
                try:
                    reply_box = self._page.wait_for_selector(sel, timeout=5000)
                    if reply_box:
                        break
                except Exception:
                    continue

            if not reply_box:
                return {"status": "error", "message": "Could not find reply box"}

            reply_box.click()
            time.sleep(0.5)
            reply_box.type(reply_text, delay=30)
            time.sleep(1)

            # Click Reply button
            reply_btn = None
            btn_selectors = [
                'button[data-testid="tweetButton"]',
                'button[data-testid="tweetButtonInline"]',
            ]

            for sel in btn_selectors:
                try:
                    reply_btn = self._page.wait_for_selector(sel, timeout=3000)
                    if reply_btn:
                        break
                except Exception:
                    continue

            if not reply_btn:
                return {"status": "error", "message": "Could not find Reply button"}

            reply_btn.click()
            time.sleep(3)

            logger.info("Reply posted to %s", tweet_url)
            return {"status": "success", "message": f"Reply posted to {tweet_url}"}

        except Exception as e:
            logger.error("reply_to_tweet failed: %s", e)
            return {"status": "error", "message": str(e)}

    def like_tweet(self, tweet_url: str) -> dict:
        """Like a specific tweet.

        Args:
            tweet_url: Full URL of the tweet to like.

        Returns:
            dict with status and details.
        """
        try:
            self._page.goto(tweet_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)

            like_btn = self._page.query_selector('button[data-testid="like"]')
            if not like_btn:
                # Check if already liked
                unlike_btn = self._page.query_selector('button[data-testid="unlike"]')
                if unlike_btn:
                    return {"status": "success", "message": "Tweet already liked"}
                return {"status": "error", "message": "Could not find like button"}

            like_btn.click()
            time.sleep(1)

            logger.info("Tweet liked: %s", tweet_url)
            return {"status": "success", "message": f"Tweet liked: {tweet_url}"}

        except Exception as e:
            logger.error("like_tweet failed: %s", e)
            return {"status": "error", "message": str(e)}

    def get_my_tweets(self, limit: int = 10) -> dict:
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

            self._page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)

            tweets = []
            tweet_elements = self._page.query_selector_all('article[data-testid="tweet"]')

            for el in tweet_elements[:limit]:
                try:
                    text_el = el.query_selector('div[data-testid="tweetText"]')
                    text = text_el.inner_text() if text_el else ""

                    time_el = el.query_selector("time")
                    timestamp = time_el.get_attribute("datetime") if time_el else ""

                    # Get tweet URL from the timestamp link
                    link_el = el.query_selector('a[href*="/status/"]')
                    url = f"https://x.com{link_el.get_attribute('href')}" if link_el else ""

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

    bot = TwitterBot(headless=False)
    bot.start()

    try:
        if not bot.is_logged_in():
            print("Not logged in. Starting interactive login...")
            if not bot.login_interactive():
                print("Login failed. Exiting.")
                sys.exit(1)
        else:
            print("Already logged in!")

        if len(sys.argv) > 1:
            action = sys.argv[1]
            if action == "post" and len(sys.argv) > 2:
                result = bot.post_tweet(" ".join(sys.argv[2:]))
                print(json.dumps(result, indent=2))
            elif action == "reply" and len(sys.argv) > 3:
                result = bot.reply_to_tweet(sys.argv[2], " ".join(sys.argv[3:]))
                print(json.dumps(result, indent=2))
            elif action == "like" and len(sys.argv) > 2:
                result = bot.like_tweet(sys.argv[2])
                print(json.dumps(result, indent=2))
            elif action == "tweets":
                result = bot.get_my_tweets()
                print(json.dumps(result, indent=2))
            elif action == "login":
                print("Login mode — session saved.")
            else:
                print("Usage: python twitter_bot.py [post <text>|reply <url> <text>|like <url>|tweets|login]")
        else:
            print("Logged in. Use: post <text>, reply <url> <text>, like <url>, tweets, login")
    finally:
        bot.stop()
