# Skill: LinkedIn Poster

## Purpose
Manage LinkedIn operations: create posts, comment on posts, like posts, and get recent posts via the fte-linkedin MCP server (Playwright-based browser automation).

## Platform
linkedin

## Inputs
- Action file path (LI_*.md in Needs_Action/)
- Action type: `create_post`, `comment_post`, `like_post`, `get_posts`

## Steps

1. **Read the action file** at the provided path. Parse YAML frontmatter for:
   - `action`: The operation to perform
   - `text`: Post/comment content
   - `post_url`: Target post URL (for comments/likes)
   - `workflow_id`: Cross-domain workflow link (if present)

2. **Create approval request** — ALL posts and comments require approval:
   - Create `APPROVAL_linkedin_{action}_{timestamp}.md` in `Pending_Approval/`
   - Include the full post content for owner review
   - Include context (post URL for comments)
   - Do NOT execute the action until approved
   - Stop processing and wait for approval

3. **After approval**: Invoke the appropriate MCP tool:
   - `create_post` → `create_linkedin_post` tool
   - `comment_post` → `comment_on_linkedin_post` tool
   - `like_post` → `like_linkedin_post` tool

4. **Log the result** using the audit logger:
   - action_type: `li_post_created` or `li_comment_posted` or `li_post_liked`
   - mcp_server: `fte-linkedin`
   - domain: `linkedin`
   - Include workflow_id if present

5. **Update Dashboard.md** with latest social media data.

## Approval Rules
- **ALL posts and comments MUST be approved before execution**
- Likes do NOT require approval
- No LinkedIn content is ever published without human approval

## Output Format
Write a summary to `Done/SUMMARY_LI_{action}_{timestamp}.md` with:
- Action performed
- Post URL (if available)
- Preview of content posted

## Technical Notes
- LinkedIn MCP uses Playwright (browser automation), not API
- Session must be pre-established: `uv run python src/playwright/linkedin_bot.py login`
- If session expired: Log error, notify owner to re-login
- LinkedIn uses Quill editor — text typed via DOM selectors

## Error Handling
- If session expired: Log error, create notification file for owner to re-login
- If browser crash: Log error, attempt restart, notify owner if persistent
- If element not found: Log with DOM details, likely LinkedIn UI changed
