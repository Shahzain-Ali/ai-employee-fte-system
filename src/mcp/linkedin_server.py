"""MCP Server: fte-linkedin — LinkedIn automation via Official API."""
import os
import sys
import json
import logging

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [fte-linkedin] %(message)s")
logger = logging.getLogger("fte-linkedin")

mcp = FastMCP("fte-linkedin")

# LinkedIn API Configuration
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_ORGANIZATION_URN = os.getenv("LINKEDIN_ORGANIZATION_URN", "")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN", "")  # For personal posts
LINKEDIN_API_VERSION = "202401"


def get_headers():
    """Get LinkedIn API headers."""
    return {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": LINKEDIN_API_VERSION
    }


def get_author_urn():
    """Get the author URN (person first, then organization)."""
    # Prefer person URN for posting (organization requires admin permissions)
    if LINKEDIN_PERSON_URN:
        return LINKEDIN_PERSON_URN
    elif LINKEDIN_ORGANIZATION_URN:
        return LINKEDIN_ORGANIZATION_URN
    else:
        # Try to get person URN from API
        try:
            resp = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return f"urn:li:person:{data.get('sub', '')}"
        except Exception as e:
            logger.error(f"Failed to get person URN: {e}")
    return None


@mcp.tool()
def create_linkedin_post(text: str) -> str:
    """Create a new post on LinkedIn.

    Args:
        text: Post content text.
    """
    if not LINKEDIN_ACCESS_TOKEN:
        return "Error: LINKEDIN_ACCESS_TOKEN not configured in .env"

    author = get_author_urn()
    if not author:
        return "Error: No LinkedIn author URN found. Set LINKEDIN_ORGANIZATION_URN or LINKEDIN_PERSON_URN in .env"

    try:
        # LinkedIn Posts API endpoint
        url = "https://api.linkedin.com/v2/ugcPosts"

        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        response = requests.post(url, headers=get_headers(), json=payload, timeout=30)

        if response.status_code in [200, 201]:
            result = response.json()
            post_id = result.get("id", "unknown")
            logger.info(f"LinkedIn post created: {post_id}")
            return json.dumps({
                "success": True,
                "post_id": post_id,
                "message": f"Post created successfully: {text[:50]}..."
            })
        else:
            error_msg = response.text
            logger.error(f"LinkedIn API error: {response.status_code} - {error_msg}")
            return json.dumps({
                "success": False,
                "error": f"API Error {response.status_code}: {error_msg}"
            })

    except Exception as e:
        logger.error(f"create_linkedin_post failed: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def get_linkedin_posts(limit: int = 10) -> str:
    """Get recent posts from the LinkedIn profile/organization.

    Args:
        limit: Maximum number of posts to return.
    """
    if not LINKEDIN_ACCESS_TOKEN:
        return json.dumps({"error": "LINKEDIN_ACCESS_TOKEN not configured"})

    author = get_author_urn()
    if not author:
        return json.dumps({"error": "No LinkedIn author URN found"})

    try:
        # Get posts by author
        url = f"https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({author})&count={limit}"

        response = requests.get(url, headers=get_headers(), timeout=30)

        if response.status_code == 200:
            data = response.json()
            posts = []
            for element in data.get("elements", []):
                post = {
                    "id": element.get("id"),
                    "text": element.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text", ""),
                    "created": element.get("created", {}).get("time"),
                    "visibility": element.get("visibility", {})
                }
                posts.append(post)
            return json.dumps({"success": True, "posts": posts})
        else:
            return json.dumps({"success": False, "error": f"API Error: {response.status_code}"})

    except Exception as e:
        logger.error(f"get_linkedin_posts failed: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def comment_on_linkedin_post(post_url: str, text: str) -> str:
    """Comment on a specific LinkedIn post.

    Args:
        post_url: Full URL of the LinkedIn post.
        text: Comment content.
    """
    if not LINKEDIN_ACCESS_TOKEN:
        return json.dumps({"error": "LINKEDIN_ACCESS_TOKEN not configured"})

    # Extract post URN from URL (format: urn:li:share:XXXXX or urn:li:ugcPost:XXXXX)
    # LinkedIn URLs: linkedin.com/posts/... or linkedin.com/feed/update/urn:li:activity:...

    try:
        # For now, return a message about manual commenting
        # Full comment API requires additional permissions
        return json.dumps({
            "success": False,
            "message": "Comment API requires additional LinkedIn permissions. Please comment manually.",
            "post_url": post_url
        })
    except Exception as e:
        logger.error(f"comment_on_linkedin_post failed: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def like_linkedin_post(post_url: str) -> str:
    """Like a specific LinkedIn post.

    Args:
        post_url: Full URL of the LinkedIn post to like.
    """
    if not LINKEDIN_ACCESS_TOKEN:
        return json.dumps({"error": "LINKEDIN_ACCESS_TOKEN not configured"})

    try:
        # Like API requires extracting activity URN from URL
        # For now, return a message
        return json.dumps({
            "success": False,
            "message": "Like API requires activity URN extraction. Please like manually.",
            "post_url": post_url
        })
    except Exception as e:
        logger.error(f"like_linkedin_post failed: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def get_linkedin_profile() -> str:
    """Get the authenticated LinkedIn user's profile info."""
    if not LINKEDIN_ACCESS_TOKEN:
        return json.dumps({"error": "LINKEDIN_ACCESS_TOKEN not configured"})

    try:
        # Get basic profile using userinfo endpoint (OpenID Connect)
        url = "https://api.linkedin.com/v2/userinfo"

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return json.dumps({
                "success": True,
                "profile": {
                    "id": data.get("sub"),
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "picture": data.get("picture")
                }
            })
        else:
            return json.dumps({"success": False, "error": f"API Error: {response.status_code}"})

    except Exception as e:
        logger.error(f"get_linkedin_profile failed: {e}")
        return json.dumps({"success": False, "error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")
