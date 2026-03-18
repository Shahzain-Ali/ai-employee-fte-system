# MCP Server Contract: fte-instagram

**Server Name**: `fte-instagram`
**Transport**: stdio
**Language**: Python (mcp SDK)
**Source**: `src/mcp/instagram_server.py`
**Backend**: Meta Graph API v21.0+ — Instagram Content Publishing API

---

## Tools

### 1. create_ig_post

**Description**: Publish an image post to Instagram Business account (2-step container flow).

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "image_url": {
      "type": "string",
      "description": "Public URL of the image to post"
    },
    "caption": {
      "type": "string",
      "description": "Post caption text (can include hashtags)"
    }
  },
  "required": ["image_url", "caption"]
}
```

**Success Response**: `"Instagram post published. Media ID: {media_id}"`

**Error Response**: `"Error publishing post: {error_message}"`

**Notes**: Uses 2-step flow: POST /{ig-user-id}/media (create container) → POST /{ig-user-id}/media_publish (publish). Daily limit: 25 posts per account.

---

### 2. create_ig_reel

**Description**: Publish a Reel (short video) to Instagram Business account.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "video_url": {
      "type": "string",
      "description": "Public URL of the video file"
    },
    "caption": {
      "type": "string",
      "description": "Reel caption text"
    }
  },
  "required": ["video_url", "caption"]
}
```

**Success Response**: `"Instagram reel published. Media ID: {media_id}"`

**Notes**: Uses media_type=REELS in the container creation step.

---

### 3. get_ig_media

**Description**: Get recent media posts from the Instagram Business account.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "integer",
      "default": 10,
      "description": "Maximum number of media items to return"
    }
  }
}
```

**Success Response**: JSON list of media with id, media_type, caption, timestamp, like_count, comments_count, permalink.

---

### 4. get_ig_comments

**Description**: Get comments on a specific Instagram media post.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "media_id": {
      "type": "string",
      "description": "Instagram media ID"
    },
    "limit": {
      "type": "integer",
      "default": 25
    }
  },
  "required": ["media_id"]
}
```

**Success Response**: JSON list of comments with id, text, username, timestamp.

---

### 5. reply_ig_comment

**Description**: Reply to a specific comment on an Instagram post.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "comment_id": {
      "type": "string",
      "description": "Instagram comment ID to reply to"
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

### 6. get_ig_insights

**Description**: Get engagement analytics for the Instagram Business account.

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

**Success Response**: JSON with impressions, reach, profile_views, follower_count for the period.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `IG_USER_ID` | Yes | Instagram Business Account ID |
| `IG_ACCESS_TOKEN` | Yes | Page Access Token linked to IG account |
| `META_API_VERSION` | No | API version (default: `v21.0`) |

## Error Handling

- Account not Business type → Return clear error: "Instagram account must be converted to Business or Creator type"
- Publishing limit reached (25/day) → Return limit message with count used today
- Invalid/expired token → Return error, create notification for owner
- Container creation fails → Return error, do not attempt publish step
- All errors logged with `mcp_server: "fte-instagram"`
