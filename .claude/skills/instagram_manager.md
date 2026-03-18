# Skill: Instagram Manager

## Purpose
Manage Instagram Business/Creator account operations: publish images and reels, read media, reply to comments, and generate insights via the fte-instagram MCP server.

## Platform
instagram

## Inputs
- Action file path (IG_*.md in Needs_Action/)
- Action type: `create_post`, `create_reel`, `reply_comment`, `get_insights`

## Steps

1. **Read the action file** at the provided path. Parse YAML frontmatter for:
   - `action`: The operation to perform
   - `caption`: Post/reel caption
   - `image_url`: Public image URL (for posts)
   - `video_url`: Public video URL (for reels)
   - `comment_id`: Target comment ID (for replies)
   - `reply_message`: Reply text
   - `workflow_id`: Cross-domain workflow link (if present)

2. **Create approval request** — ALL Instagram publishing actions require approval:
   - Create `APPROVAL_instagram_{action}_{timestamp}.md` in `Pending_Approval/`
   - Include the full caption/message content for owner review
   - Include image/video URL for context
   - Do NOT execute the action until approved
   - Stop processing and wait for approval

3. **After approval**: Invoke the appropriate MCP tool:
   - `create_post` → `create_ig_post` tool (2-step: container → publish)
   - `create_reel` → `create_ig_reel` tool (2-step: container → publish)
   - `reply_comment` → `reply_ig_comment` tool

4. **Log the result** using the audit logger:
   - action_type: `ig_post_published`, `ig_reel_published`, or `ig_comment_replied`
   - mcp_server: `fte-instagram`
   - domain: `instagram`
   - Include workflow_id if present

5. **Track daily post count** — Instagram has a 50 posts/day limit:
   - Check today's audit log for ig_post_published and ig_reel_published counts
   - If approaching limit (45+), warn in response
   - If at limit (50), reject the action with clear message

6. **Update Dashboard.md** with latest social media data.

## Approval Rules
- **ALL posts, reels, and replies MUST be approved before execution**
- No Instagram content is ever published without human approval

## Output Format
Write a summary to `Done/SUMMARY_IG_{action}_{timestamp}.md` with:
- Action performed
- Media ID from Instagram
- Preview of content posted
- Permalink to the published content

## Error Handling
- If account not Business/Creator: Return clear error message explaining the requirement
- If token expired: Log error, create notification file for owner
- If publishing limit reached: Return limit message with count used today
- If container creation fails: Return error, do not attempt publish step
