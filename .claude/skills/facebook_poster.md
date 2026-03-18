# Skill: Facebook Poster

## Purpose
Manage Facebook Business Page operations: create posts, read engagement, reply to comments, and generate insights via the fte-facebook MCP server.

## Platform
facebook

## Inputs
- Action file path (FB_*.md in Needs_Action/)
- Action type: `create_post`, `reply_comment`, `get_insights`

## Steps

1. **Read the action file** at the provided path. Parse YAML frontmatter for:
   - `action`: The operation to perform
   - `message`: Post/reply content
   - `post_id`: Target post ID (for replies/comments)
   - `comment_id`: Target comment ID (for replies)
   - `workflow_id`: Cross-domain workflow link (if present)

2. **Create approval request** — ALL Facebook posts and replies require approval:
   - Create `APPROVAL_facebook_{action}_{timestamp}.md` in `Pending_Approval/`
   - Include the full message content for owner review
   - Include context (post ID for replies, comment text being replied to)
   - Do NOT execute the action until approved
   - Stop processing and wait for approval

3. **After approval**: Invoke the appropriate MCP tool:
   - `create_post` → `create_page_post` tool
   - `reply_comment` → `reply_to_comment` tool

4. **Log the result** using the audit logger:
   - action_type: `fb_post_created` or `fb_comment_replied`
   - mcp_server: `fte-facebook`
   - domain: `facebook`
   - Include workflow_id if present

5. **Update Dashboard.md** with latest social media data.

## Approval Rules
- **ALL posts and replies MUST be approved before execution**
- No Facebook content is ever published without human approval

## Output Format
Write a summary to `Done/SUMMARY_FB_{action}_{timestamp}.md` with:
- Action performed
- Post/comment ID from Facebook
- Preview of content posted

## Error Handling
- If token expired: Log error, create notification file for owner to regenerate token
- If rate limited: Log warning, pause operations, include rate limit info in response
- If permission denied: Log error with specific permission needed
