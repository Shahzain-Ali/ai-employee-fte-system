# Skill: Twitter/X Poster

## Purpose
Manage Twitter/X operations: post tweets, reply to tweets, like tweets, and get recent tweets via the fte-twitter MCP server (Playwright-based browser automation).

## Platform
twitter

## Inputs
- Action file path (TW_*.md in Needs_Action/)
- Action type: `post_tweet`, `reply_tweet`, `like_tweet`, `get_tweets`

## Steps

1. **Read the action file** at the provided path. Parse YAML frontmatter for:
   - `action`: The operation to perform
   - `text`: Tweet/reply content (max 280 characters)
   - `tweet_url`: Target tweet URL (for replies/likes)
   - `workflow_id`: Cross-domain workflow link (if present)

2. **Create approval request** — ALL tweets and replies require approval:
   - Create `APPROVAL_twitter_{action}_{timestamp}.md` in `Pending_Approval/`
   - Include the full tweet content for owner review
   - Include context (tweet URL for replies, original tweet text)
   - Do NOT execute the action until approved
   - Stop processing and wait for approval

3. **After approval**: Invoke the appropriate MCP tool:
   - `post_tweet` → `post_tweet` tool
   - `reply_tweet` → `reply_to_tweet` tool
   - `like_tweet` → `like_tweet` tool

4. **Log the result** using the audit logger:
   - action_type: `tw_tweet_posted` or `tw_reply_posted` or `tw_tweet_liked`
   - mcp_server: `fte-twitter`
   - domain: `twitter`
   - Include workflow_id if present

5. **Update Dashboard.md** with latest social media data.

## Approval Rules
- **ALL tweets and replies MUST be approved before execution**
- Likes do NOT require approval
- No tweet content is ever published without human approval

## Output Format
Write a summary to `Done/SUMMARY_TW_{action}_{timestamp}.md` with:
- Action performed
- Tweet URL (if available)
- Preview of content posted

## Technical Notes
- Twitter MCP uses Playwright (browser automation), not API
- Session must be pre-established: `uv run python src/playwright/twitter_bot.py login`
- If session expired: Log error, notify owner to re-login
- Tweet text limit: 280 characters

## Error Handling
- If session expired: Log error, create notification file for owner to re-login
- If browser crash: Log error, attempt restart, notify owner if persistent
- If element not found: Log with DOM details, likely Twitter UI changed
