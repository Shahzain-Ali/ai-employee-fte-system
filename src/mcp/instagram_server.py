"""MCP Server: fte-instagram — Instagram Business/Creator Account via Meta Graph API."""
import os
import sys
import json
import logging
import time

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [fte-instagram] %(message)s")
logger = logging.getLogger("fte-instagram")

_client = None


def _get_client():
    """Get or create the Meta Graph API client."""
    global _client
    if _client is None:
        from src.mcp._meta_client import MetaGraphClient
        token = os.getenv("IG_ACCESS_TOKEN", "")
        version = os.getenv("META_API_VERSION", "v21.0")
        if not token:
            raise RuntimeError("IG_ACCESS_TOKEN not set in environment")
        _client = MetaGraphClient(access_token=token, api_version=version)
    return _client


IG_USER_ID = os.getenv("IG_USER_ID", "")

mcp = FastMCP("fte-instagram")


def _wait_for_container(client, container_id: str, max_wait: int = 60) -> str:
    """Poll container status until it's ready for publishing.

    Args:
        client: MetaGraphClient instance.
        container_id: The media container ID.
        max_wait: Maximum seconds to wait.

    Returns:
        Container status string.
    """
    for _ in range(max_wait // 2):
        result = client.get(f"/{container_id}", {"fields": "status_code"})
        status = result.get("status_code", "")
        if status == "FINISHED":
            return status
        if status == "ERROR":
            return status
        time.sleep(2)
    return "TIMEOUT"


@mcp.tool()
def create_ig_post(image_url: str, caption: str) -> str:
    """Publish an image post to Instagram (2-step container flow).

    Args:
        image_url: Public URL of the image to post.
        caption: Post caption text (can include hashtags).
    """
    try:
        if not IG_USER_ID:
            return "Error: IG_USER_ID not configured. Convert your Instagram account to Business or Creator type."

        client = _get_client()

        # Step 1: Create media container
        container = client.post(f"/{IG_USER_ID}/media", {
            "image_url": image_url,
            "caption": caption,
        })
        container_id = container.get("id")
        if not container_id:
            return "Error: Failed to create media container"

        # Wait for container processing
        status = _wait_for_container(client, container_id)
        if status != "FINISHED":
            return f"Error: Media container processing failed (status: {status})"

        # Step 2: Publish
        result = client.post(f"/{IG_USER_ID}/media_publish", {
            "creation_id": container_id,
        })
        media_id = result.get("id", "unknown")
        return f"Instagram post published. Media ID: {media_id}"
    except Exception as e:
        logger.error("create_ig_post failed: %s", e)
        return f"Error publishing post: {e}"


@mcp.tool()
def create_ig_reel(video_url: str, caption: str) -> str:
    """Publish a Reel (short video) to Instagram (2-step container flow).

    Args:
        video_url: Public URL of the video file.
        caption: Reel caption text.
    """
    try:
        if not IG_USER_ID:
            return "Error: IG_USER_ID not configured. Convert your Instagram account to Business or Creator type."

        client = _get_client()

        # Step 1: Create reel container
        container = client.post(f"/{IG_USER_ID}/media", {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
        })
        container_id = container.get("id")
        if not container_id:
            return "Error: Failed to create reel container"

        # Wait for video processing (can take longer)
        status = _wait_for_container(client, container_id, max_wait=120)
        if status != "FINISHED":
            return f"Error: Reel container processing failed (status: {status})"

        # Step 2: Publish
        result = client.post(f"/{IG_USER_ID}/media_publish", {
            "creation_id": container_id,
        })
        media_id = result.get("id", "unknown")
        return f"Instagram reel published. Media ID: {media_id}"
    except Exception as e:
        logger.error("create_ig_reel failed: %s", e)
        return f"Error publishing reel: {e}"


@mcp.tool()
def get_ig_media(limit: int = 10) -> str:
    """Get recent media posts from the Instagram account.

    Args:
        limit: Maximum number of media items to return.
    """
    try:
        if not IG_USER_ID:
            return "Error: IG_USER_ID not configured"

        client = _get_client()
        result = client.get(f"/{IG_USER_ID}/media", {
            "fields": "id,media_type,caption,timestamp,like_count,comments_count,permalink",
            "limit": limit,
        })

        media = []
        for item in result.get("data", []):
            media.append({
                "id": item.get("id", ""),
                "media_type": item.get("media_type", ""),
                "caption": (item.get("caption", "") or "")[:200],
                "timestamp": item.get("timestamp", ""),
                "like_count": item.get("like_count", 0),
                "comments_count": item.get("comments_count", 0),
                "permalink": item.get("permalink", ""),
            })

        return json.dumps(media, indent=2)
    except Exception as e:
        logger.error("get_ig_media failed: %s", e)
        return f"Error getting media: {e}"


@mcp.tool()
def get_ig_comments(media_id: str, limit: int = 25) -> str:
    """Get comments on a specific Instagram media post.

    Args:
        media_id: Instagram media ID.
        limit: Maximum number of comments to return.
    """
    try:
        client = _get_client()
        result = client.get(f"/{media_id}/comments", {
            "fields": "id,text,username,timestamp",
            "limit": limit,
        })

        comments = []
        for c in result.get("data", []):
            comments.append({
                "id": c.get("id", ""),
                "text": c.get("text", ""),
                "username": c.get("username", ""),
                "timestamp": c.get("timestamp", ""),
            })

        return json.dumps(comments, indent=2)
    except Exception as e:
        logger.error("get_ig_comments failed: %s", e)
        return f"Error getting comments: {e}"


@mcp.tool()
def reply_ig_comment(comment_id: str, message: str) -> str:
    """Reply to a specific comment on an Instagram post.

    Args:
        comment_id: Instagram comment ID to reply to.
        message: Reply text.
    """
    try:
        client = _get_client()
        result = client.post(f"/{comment_id}/replies", {"message": message})
        reply_id = result.get("id", "unknown")
        return f"Reply posted. Comment ID: {reply_id}"
    except Exception as e:
        logger.error("reply_ig_comment failed: %s", e)
        return f"Error replying to comment: {e}"


@mcp.tool()
def get_ig_insights(period: str = "week") -> str:
    """Get engagement analytics for the Instagram account.

    Args:
        period: Time period for insights (day, week, days_28).
    """
    try:
        if not IG_USER_ID:
            return "Error: IG_USER_ID not configured"

        client = _get_client()
        result = client.get(f"/{IG_USER_ID}/insights", {
            "metric": "impressions,reach,profile_views",
            "period": period if period != "week" else "day",
        })

        insights = {}
        for item in result.get("data", []):
            name = item.get("name", "")
            values = item.get("values", [{}])
            insights[name] = values[-1].get("value", 0) if values else 0

        # Get follower count separately
        profile = client.get(f"/{IG_USER_ID}", {"fields": "followers_count"})

        return json.dumps({
            "period": period,
            "impressions": insights.get("impressions", 0),
            "reach": insights.get("reach", 0),
            "profile_views": insights.get("profile_views", 0),
            "follower_count": profile.get("followers_count", 0),
        }, indent=2)
    except Exception as e:
        logger.error("get_ig_insights failed: %s", e)
        return f"Error getting insights: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
