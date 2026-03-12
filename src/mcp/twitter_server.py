"""MCP Server: fte-twitter — Twitter/X automation via Playwright browser."""
import os
import sys
import json
import logging
import atexit

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [fte-twitter] %(message)s")
logger = logging.getLogger("fte-twitter")

mcp = FastMCP("fte-twitter")

# Lazy-initialized bot instance (shared across tool calls)
_bot = None


async def _get_bot():
    """Get or create the Twitter Playwright bot instance."""
    global _bot
    if _bot is None:
        from src.playwright.twitter_bot import TwitterBot
        headless = os.getenv("TWITTER_HEADLESS", "true").lower() == "true"
        bot = TwitterBot(headless=headless)
        await bot.start()

        if not await bot.is_logged_in():
            await bot.stop()
            logger.error("Twitter bot is NOT logged in. Run setup first: "
                         "uv run python src/playwright/twitter_bot.py login")
            raise RuntimeError(
                "Twitter session not found. Run setup first:\n"
                "  uv run python src/playwright/twitter_bot.py login\n"
                "This opens a browser for manual login. Session is saved for reuse."
            )

        _bot = bot
        logger.info("Twitter bot initialized and logged in")
    return _bot


@mcp.tool()
async def post_tweet(text: str) -> str:
    """Post a new tweet on Twitter/X.

    Args:
        text: Tweet content (max 280 characters).
    """
    try:
        bot = await _get_bot()
        result = await bot.post_tweet(text)
        if result["status"] == "success":
            return f"Tweet posted successfully: {text[:100]}"
        return f"Error posting tweet: {result['message']}"
    except Exception as e:
        logger.error("post_tweet failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def get_my_tweets(limit: int = 10) -> str:
    """Get recent tweets from the logged-in user's profile.

    Args:
        limit: Maximum number of tweets to return.
    """
    try:
        bot = await _get_bot()
        result = await bot.get_my_tweets(limit=limit)
        if result["status"] == "success":
            return json.dumps(result["tweets"], indent=2)
        return f"Error getting tweets: {result['message']}"
    except Exception as e:
        logger.error("get_my_tweets failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def reply_to_tweet(tweet_url: str, text: str) -> str:
    """Reply to a specific tweet on Twitter/X.

    Args:
        tweet_url: Full URL of the tweet (e.g. https://x.com/user/status/123).
        text: Reply content.
    """
    try:
        bot = await _get_bot()
        result = await bot.reply_to_tweet(tweet_url, text)
        if result["status"] == "success":
            return f"Reply posted successfully to {tweet_url}"
        return f"Error replying: {result['message']}"
    except Exception as e:
        logger.error("reply_to_tweet failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def like_tweet(tweet_url: str) -> str:
    """Like a specific tweet on Twitter/X.

    Args:
        tweet_url: Full URL of the tweet to like.
    """
    try:
        bot = await _get_bot()
        result = await bot.like_tweet(tweet_url)
        if result["status"] == "success":
            return f"Tweet liked: {tweet_url}"
        return f"Error liking tweet: {result['message']}"
    except Exception as e:
        logger.error("like_tweet failed: %s", e)
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
