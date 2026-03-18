"""MCP Server: fte-facebook — Facebook Business Page via Meta Graph API."""
import os
import sys
import json
import logging

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [fte-facebook] %(message)s")
logger = logging.getLogger("fte-facebook")

# Lazy import to allow server to start even if meta_client has issues
_client = None


def _get_client():
    """Get or create the Meta Graph API client."""
    global _client
    if _client is None:
        from src.mcp._meta_client import MetaGraphClient
        token = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
        version = os.getenv("META_API_VERSION", "v25.0")
        if not token:
            raise RuntimeError("FB_PAGE_ACCESS_TOKEN not set in environment")
        _client = MetaGraphClient(access_token=token, api_version=version)
    return _client


FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")

mcp = FastMCP("fte-facebook")


@mcp.tool()
def create_page_post(message: str, link: str = "") -> str:
    """Create a new post on the Facebook Business Page.

    Args:
        message: Post text content.
        link: Optional URL to share with the post.
    """
    try:
        if not FB_PAGE_ID:
            return "Error: FB_PAGE_ID not configured in environment"

        client = _get_client()
        data = {"message": message}
        if link:
            data["link"] = link

        result = client.post(f"/{FB_PAGE_ID}/feed", data=data)
        post_id = result.get("id", "unknown")
        return f"Post created on Facebook Page. Post ID: {post_id}"
    except Exception as e:
        logger.error("create_page_post failed: %s", e)
        return f"Error creating post: {e}"


@mcp.tool()
def get_page_posts(limit: int = 10) -> str:
    """Get recent posts from the Facebook Business Page.

    Args:
        limit: Maximum number of posts to return.
    """
    try:
        if not FB_PAGE_ID:
            return "Error: FB_PAGE_ID not configured in environment"

        client = _get_client()
        result = client.get(f"/{FB_PAGE_ID}/feed", {
            "fields": "id,message,created_time,likes.summary(true),comments.summary(true),shares",
            "limit": limit,
        })

        posts = []
        for post in result.get("data", []):
            posts.append({
                "id": post.get("id", ""),
                "message": post.get("message", "")[:200],
                "created_time": post.get("created_time", ""),
                "likes_count": post.get("likes", {}).get("summary", {}).get("total_count", 0),
                "comments_count": post.get("comments", {}).get("summary", {}).get("total_count", 0),
                "shares_count": post.get("shares", {}).get("count", 0),
            })

        return json.dumps(posts, indent=2)
    except Exception as e:
        logger.error("get_page_posts failed: %s", e)
        return f"Error getting posts: {e}"


@mcp.tool()
def get_post_comments(post_id: str, limit: int = 25) -> str:
    """Get comments on a specific Facebook post.

    Args:
        post_id: Facebook post ID.
        limit: Maximum number of comments to return.
    """
    try:
        client = _get_client()
        result = client.get(f"/{post_id}/comments", {
            "fields": "id,message,from,created_time",
            "limit": limit,
        })

        comments = []
        for c in result.get("data", []):
            comments.append({
                "id": c.get("id", ""),
                "message": c.get("message", ""),
                "from_name": c.get("from", {}).get("name", ""),
                "created_time": c.get("created_time", ""),
            })

        return json.dumps(comments, indent=2)
    except Exception as e:
        logger.error("get_post_comments failed: %s", e)
        return f"Error getting comments: {e}"


@mcp.tool()
def reply_to_comment(comment_id: str, message: str) -> str:
    """Reply to a specific comment on a Facebook post.

    Args:
        comment_id: Facebook comment ID to reply to.
        message: Reply text.
    """
    try:
        client = _get_client()
        result = client.post(f"/{comment_id}/comments", {"message": message})
        reply_id = result.get("id", "unknown")
        return f"Reply posted. Comment ID: {reply_id}"
    except Exception as e:
        logger.error("reply_to_comment failed: %s", e)
        return f"Error replying to comment: {e}"


@mcp.tool()
def get_page_insights(period: str = "week") -> str:
    """Get engagement analytics for the Facebook Page.

    Args:
        period: Time period for insights (day, week, days_28).
    """
    try:
        if not FB_PAGE_ID:
            return "Error: FB_PAGE_ID not configured in environment"

        client = _get_client()
        result = client.get(f"/{FB_PAGE_ID}/insights", {
            "metric": "page_views_total,page_post_engagements,page_fan_adds",
            "period": period,
        })

        insights = {}
        for item in result.get("data", []):
            name = item.get("name", "")
            values = item.get("values", [{}])
            insights[name] = values[-1].get("value", 0) if values else 0

        return json.dumps({
            "period": period,
            "page_views": insights.get("page_views_total", 0),
            "post_engagement": insights.get("page_post_engagements", 0),
            "new_followers": insights.get("page_fan_adds", 0),
        }, indent=2)
    except Exception as e:
        logger.error("get_page_insights failed: %s", e)
        return f"Error getting insights: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
