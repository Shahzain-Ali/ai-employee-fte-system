"""MCP Server: fte-linkedin — LinkedIn automation via Playwright browser."""
import os
import sys
import json
import logging
import atexit

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [fte-linkedin] %(message)s")
logger = logging.getLogger("fte-linkedin")

mcp = FastMCP("fte-linkedin")

# Lazy-initialized bot instance (shared across tool calls)
_bot = None


def _get_bot():
    """Get or create the LinkedIn Playwright bot instance."""
    global _bot
    if _bot is None:
        from src.playwright.linkedin_bot import LinkedInBot
        headless = os.getenv("LINKEDIN_HEADLESS", "true").lower() == "true"
        _bot = LinkedInBot(headless=headless)
        _bot.start()

        if not _bot.is_logged_in():
            logger.error("LinkedIn bot is NOT logged in. Run setup first: "
                         "uv run python src/playwright/linkedin_bot.py login")
            raise RuntimeError(
                "LinkedIn session not found. Run setup first:\n"
                "  uv run python src/playwright/linkedin_bot.py login\n"
                "This opens a browser for manual login. Session is saved for reuse."
            )

        logger.info("LinkedIn bot initialized and logged in")
        atexit.register(_cleanup)
    return _bot


def _cleanup():
    """Cleanup bot on exit."""
    global _bot
    if _bot:
        try:
            _bot.stop()
        except Exception:
            pass
        _bot = None


@mcp.tool()
def create_linkedin_post(text: str) -> str:
    """Create a new post on LinkedIn.

    Args:
        text: Post content text.
    """
    try:
        bot = _get_bot()
        result = bot.create_post(text)
        if result["status"] == "success":
            return f"LinkedIn post created successfully: {text[:100]}"
        return f"Error creating post: {result['message']}"
    except Exception as e:
        logger.error("create_linkedin_post failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
def get_linkedin_posts(limit: int = 10) -> str:
    """Get recent posts from the logged-in user's LinkedIn profile.

    Args:
        limit: Maximum number of posts to return.
    """
    try:
        bot = _get_bot()
        result = bot.get_my_posts(limit=limit)
        if result["status"] == "success":
            return json.dumps(result["posts"], indent=2)
        return f"Error getting posts: {result['message']}"
    except Exception as e:
        logger.error("get_linkedin_posts failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
def comment_on_linkedin_post(post_url: str, text: str) -> str:
    """Comment on a specific LinkedIn post.

    Args:
        post_url: Full URL of the LinkedIn post.
        text: Comment content.
    """
    try:
        bot = _get_bot()
        result = bot.comment_on_post(post_url, text)
        if result["status"] == "success":
            return f"Comment posted on LinkedIn: {post_url}"
        return f"Error commenting: {result['message']}"
    except Exception as e:
        logger.error("comment_on_linkedin_post failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
def like_linkedin_post(post_url: str) -> str:
    """Like a specific LinkedIn post.

    Args:
        post_url: Full URL of the LinkedIn post to like.
    """
    try:
        bot = _get_bot()
        result = bot.like_post(post_url)
        if result["status"] == "success":
            return f"LinkedIn post liked: {post_url}"
        return f"Error liking post: {result['message']}"
    except Exception as e:
        logger.error("like_linkedin_post failed: %s", e)
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
