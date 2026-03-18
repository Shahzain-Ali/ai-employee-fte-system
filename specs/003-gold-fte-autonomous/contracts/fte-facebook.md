# MCP Server Contract: fte-facebook

**Server Name**: `fte-facebook`
**Transport**: stdio
**Language**: Python (mcp SDK)
**Source**: `src/mcp/facebook_server.py`
**Backend**: Meta Graph API v21.0+ (`https://graph.facebook.com/v21.0/`)

---

## Tools

### 1. create_page_post

**Description**: Create a new post on the Facebook Business Page.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "message": {
      "type": "string",
      "description": "Post text content"
    },
    "link": {
      "type": "string",
      "description": "Optional URL to share with the post"
    }
  },
  "required": ["message"]
}
```

**Success Response**: `"Post created on Facebook Page. Post ID: {post_id}"`

**Error Response**: `"Error creating post: {error_message}"`

---

### 2. get_page_posts

**Description**: Get recent posts from the Facebook Business Page.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "integer",
      "default": 10,
      "description": "Maximum number of posts to return"
    }
  }
}
```

**Success Response**: JSON list of posts with id, message, created_time, likes_count, comments_count, shares_count.

---

### 3. get_post_comments

**Description**: Get comments on a specific Facebook post.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "post_id": {
      "type": "string",
      "description": "Facebook post ID"
    },
    "limit": {
      "type": "integer",
      "default": 25
    }
  },
  "required": ["post_id"]
}
```

**Success Response**: JSON list of comments with id, message, from_name, created_time.

---

### 4. reply_to_comment

**Description**: Reply to a specific comment on a Facebook post.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "comment_id": {
      "type": "string",
      "description": "Facebook comment ID to reply to"
    },
    "message": {
      "type": "string",
      "description": "Reply text"
    }
  },
  "required": ["comment_id", "message"]
}
```

**Success Response**: `"Reply posted. Comment ID: {reply_id}"`

---

### 5. get_page_insights

**Description**: Get engagement analytics for the Facebook Page.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "period": {
      "type": "string",
      "enum": ["day", "week", "days_28"],
      "default": "week",
      "description": "Time period for insights"
    }
  }
}
```

**Success Response**: JSON with page_views, post_reach, post_engagement, new_followers for the period.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FB_PAGE_ID` | Yes | Facebook Business Page ID |
| `FB_PAGE_ACCESS_TOKEN` | Yes | Non-expiring Page Access Token |
| `META_API_VERSION` | No | API version (default: `v21.0`) |

## Error Handling

- Invalid/expired token → Return error, create notification for owner
- Rate limit (4800/24h) → Return rate limit message, pause operations
- Permission denied → Return clear message about missing permissions
- All errors logged with `mcp_server: "fte-facebook"`
