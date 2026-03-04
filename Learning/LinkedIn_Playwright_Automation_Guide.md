# LinkedIn Automation — Playwright Setup Guide

**Date:** 2026-03-04
**Author:** Shahzain Bangash + Claude Opus 4.6
**Status:** WORKING — Post tested successfully
**Method:** Playwright (Browser Automation) — No API needed

---

## Why Playwright for LinkedIn?

LinkedIn official API **posting access sirf approved partners ko milta hai** — normal developers ko nahi. Isliye hum Playwright (browser automation) use karte hain — free, no approval needed.

| Approach | Cost | Approval | Reliability |
|----------|------|----------|-------------|
| LinkedIn API | Restricted/Paid | Partner approval needed | Very stable |
| Playwright | FREE | No approval | DOM changes se break ho sakta hai |

---

## What We Can Automate

| Action | Status |
|--------|--------|
| Create Post (text) | WORKING |
| Comment on Post | Built (needs testing) |
| Like a Post | Built (needs testing) |
| Get My Posts | Built (needs testing) |
| Login Session Persistence | WORKING |

---

## Setup Steps

### Step 1: Install Dependencies

```bash
uv pip install playwright playwright-stealth
PLAYWRIGHT_BROWSERS_PATH=0 uv run playwright install chromium
```

### Step 2: First Login (One-time manual)

```bash
uv run python src/playwright/linkedin_bot.py login
```

- Chromium browser khulega
- LinkedIn login page aayega
- **Manually login karo** (email + password)
- Login hone ke baad script automatically detect karegi aur session save karegi
- Session saved in `.sessions/linkedin/`
- **Next time login ki zaroorat nahi** — session reuse hogi

### Step 3: Test Post

```bash
uv run python src/playwright/linkedin_bot.py post "Your post text here"
```

### Step 4: MCP Server (Claude Code Integration)

MCP server registered in `.mcp.json`:
```json
"fte-linkedin": {
  "type": "stdio",
  "command": "uv",
  "args": ["run", "python", "src/mcp/linkedin_server.py"]
}
```

After setup, Claude Code mein bolo:
> "LinkedIn pe post karo: Hello World!"

---

## Files Created

| File | Purpose |
|------|---------|
| `src/playwright/linkedin_bot.py` | LinkedIn browser automation bot |
| `src/mcp/linkedin_server.py` | MCP server for Claude Code integration |
| `.sessions/linkedin/` | Browser session data (login persistence) |

---

## Problems & Solutions

### Problem 1: Playwright Chromium not found
**Error:** `Executable doesn't exist at /home/.../.cache/ms-playwright/chromium-1208`
**Cause:** Playwright install with sudo fails on WSL
**Solution:** Install locally without sudo:
```bash
PLAYWRIGHT_BROWSERS_PATH=0 uv run playwright install chromium
```

### Problem 2: Windows Chrome from WSL — remote debugging pipe error
**Error:** `Remote debugging pipe file descriptors are not open`
**Cause:** Windows Chrome executable (`/mnt/c/Program Files/Google/Chrome/Application/chrome.exe`) cannot run with Playwright remote debugging from WSL
**Solution:** Don't use Windows Chrome. Use Playwright's own Chromium (installed in Step 1). Same approach as WhatsApp watcher.

### Problem 3: Login detected but "Still waiting..." keeps showing
**Error:** Script says "Still waiting... (30s elapsed)" even after login
**Cause:** `is_logged_in()` function was checking old CSS selectors that LinkedIn changed
**Solution:** Changed login detection to URL-based check instead of DOM selectors:
```python
# OLD (broken):
self._page.query_selector('div.feed-shared-update-v2') is not None

# NEW (working):
if "/login" not in current_url and "/feed" in current_url:
    return True
```

### Problem 4: "Start a post" clicking Video button instead
**Error:** `Could not find post editor` — modal shows media upload (Select files to begin)
**Cause:** Selector `button[class*="share-box"]` matches the **Video** button instead of the text "Start a post" button
**Solution:** Use specific selector for the top-bar button:
```python
# OLD (wrong — clicks Video):
'button[class*="share-box"]'

# NEW (correct — clicks Start a post):
'div.share-box-feed-entry__top-bar button'
```

### Problem 5: LinkedIn editor selector not found
**Error:** `Could not find post editor` after modal opens
**Cause:** LinkedIn uses **Quill editor** — standard textarea selectors don't work
**Solution:** LinkedIn editor selectors (from DOM inspection):
```python
# Text editor (Quill):
'div.ql-editor[contenteditable="true"]'
'div[role="textbox"][aria-label="Text editor for creating content"]'

# Post button:
'button.share-actions__primary-action'
'div.share-box button:has-text("Post")'
```

---

## Key Technical Details

### Browser Launch (Exact WhatsApp watcher pattern)
```python
self._playwright.chromium.launch_persistent_context(
    user_data_dir=str(self._session_path),
    headless=self._headless,
    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
)
stealth = Stealth()
stealth.apply_stealth_sync(self._context)
```

### LinkedIn Feed DOM Structure (March 2026)
```
div.share-box-feed-entry__closed-share-box
  ├── div.share-box-feed-entry__top-bar
  │     ├── a (profile avatar)
  │     └── button "Start a post"  ← CLICK THIS for text post
  └── div.share-box-feed-entry-toolbar__wrapper
        ├── button "Video"  ← DO NOT click
        ├── button "Photo"  ← DO NOT click
        └── a "Write article"

After clicking "Start a post":
div.artdeco-modal (share-box-v2__modal)
  ├── div.share-box
  │     ├── div.ql-editor[contenteditable="true"]  ← TYPE HERE
  │     └── button.share-actions__primary-action "Post"  ← CLICK TO POST
```

---

## Testing Checklist

- [x] `uv run python src/playwright/linkedin_bot.py login` — session saved
- [x] `uv run python src/playwright/linkedin_bot.py post "test"` — post created
- [ ] Comment on post — needs testing
- [ ] Like a post — needs testing
- [ ] MCP server via Claude Code — needs testing
- [ ] Headless mode — needs testing
