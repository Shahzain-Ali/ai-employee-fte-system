"""MCP Server: fte-linkedin — LinkedIn automation via Playwright browser."""
import os
import sys
import json
import logging

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [fte-linkedin] %(message)s")
logger = logging.getLogger("fte-linkedin")

mcp = FastMCP("fte-linkedin")

# Lazy-initialized bot instance (shared across tool calls)
_bot = None


async def _get_bot():
    """Get or create the LinkedIn Playwright bot instance."""
    global _bot
    if _bot is None:
        from src.playwright.linkedin_bot import LinkedInBot
        headless = os.getenv("LINKEDIN_HEADLESS", "true").lower() == "true"
        bot = LinkedInBot(headless=headless)
        await bot.start()

        if not await bot.is_logged_in():
            await bot.stop()
            logger.error("LinkedIn bot is NOT logged in. Run setup first: "
                         "uv run python src/playwright/linkedin_bot.py login")
            raise RuntimeError(
                "LinkedIn session not found. Run setup first:\n"
                "  uv run python src/playwright/linkedin_bot.py login\n"
                "This opens a browser for manual login. Session is saved for reuse."
            )

        _bot = bot
        logger.info("LinkedIn bot initialized and logged in")
    return _bot


@mcp.tool()
async def create_linkedin_post(text: str) -> str:
    """Create a new post on LinkedIn.

    Args:
        text: Post content text.
    """
    try:
        bot = await _get_bot()
        result = await bot.create_post(text)
        if result["status"] == "success":
            return f"LinkedIn post created successfully: {text[:100]}"
        return f"Error creating post: {result['message']}"
    except Exception as e:
        logger.error("create_linkedin_post failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def get_linkedin_posts(limit: int = 10) -> str:
    """Get recent posts from the logged-in user's LinkedIn profile.

    Args:
        limit: Maximum number of posts to return.
    """
    try:
        bot = await _get_bot()
        result = await bot.get_my_posts(limit=limit)
        if result["status"] == "success":
            return json.dumps(result["posts"], indent=2)
        return f"Error getting posts: {result['message']}"
    except Exception as e:
        logger.error("get_linkedin_posts failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def comment_on_linkedin_post(post_url: str, text: str) -> str:
    """Comment on a specific LinkedIn post.

    Args:
        post_url: Full URL of the LinkedIn post.
        text: Comment content.
    """
    try:
        bot = await _get_bot()
        result = await bot.comment_on_post(post_url, text)
        if result["status"] == "success":
            return f"Comment posted on LinkedIn: {post_url}"
        return f"Error commenting: {result['message']}"
    except Exception as e:
        logger.error("comment_on_linkedin_post failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def like_linkedin_post(post_url: str) -> str:
    """Like a specific LinkedIn post.

    Args:
        post_url: Full URL of the LinkedIn post to like.
    """
    try:
        bot = await _get_bot()
        result = await bot.like_post(post_url)
        if result["status"] == "success":
            return f"LinkedIn post liked: {post_url}"
        return f"Error liking post: {result['message']}"
    except Exception as e:
        logger.error("like_linkedin_post failed: %s", e)
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
