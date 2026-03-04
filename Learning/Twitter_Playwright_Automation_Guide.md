# Twitter/X Automation — Playwright Setup Guide

**Date:** 2026-03-04
**Author:** Shahzain Bangash + Claude Opus 4.6
**Status:** WORKING — Tweet post tested successfully
**Method:** Playwright (Browser Automation) — No paid API needed

---

## Why Playwright for Twitter/X?

Twitter/X API ab **Pay-Per-Use** hai (Feb 2026 se). Minimum $5 credits khareedne padte hain. Free tier available nahi naye developers ke liye. Isliye hum Playwright use karte hain — completely free.

| Approach | Cost | Reliability |
|----------|------|-------------|
| Twitter API (Pay-Per-Use) | $5 minimum, per-request charges | Very stable |
| Twitter API (Basic) | $200/month | Very stable |
| Playwright | FREE | DOM changes se break ho sakta hai |

### API Test Result
Humne Twitter API bhi test kiya — credentials sahi the lekin:
```
402 Payment Required
Your enrolled account does not have any credits to fulfill this request.
```
$0 credits pe API kaam nahi karta — isliye Playwright approach.

---

## What We Can Automate

| Action | Status |
|--------|--------|
| Post Tweet | WORKING |
| Reply to Tweet | Built (needs testing) |
| Like a Tweet | Built (needs testing) |
| Get My Tweets | Built (needs testing) |
| Login Session Persistence | WORKING |

---

## Setup Steps

### Step 1: Install Dependencies

```bash
uv pip install playwright playwright-stealth
PLAYWRIGHT_BROWSERS_PATH=0 uv run playwright install chromium
```

### Step 2: Twitter Developer Console Setup (Optional — for API fallback)

Agar future mein API use karna ho:
1. Go to `developer.x.com`
2. Create app (Plan: Pay Per Use)
3. User Authentication: Read and Write + Web App
4. Generate keys: API Key, API Secret, Access Token, Access Token Secret
5. Add to `.env`:
```env
TWITTER_API_KEY=your_consumer_key
TWITTER_API_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_CLIENT_ID=your_client_id
TWITTER_CLIENT_SECRET=your_client_secret
TWITTER_HANDLE=@YourHandle
```

### Step 3: First Login (One-time manual)

```bash
uv run python src/playwright/twitter_bot.py login
```

- Chromium browser khulega
- **x.com homepage** khulega (login page nahi — less suspicious)
- **IMPORTANT: "Sign in with Google" mat click karo** — Google block karega
- Instead: **"Sign up" se email add karo** ya **username + password se login karo**
- Login hone ke baad URL `x.com/home` pe redirect hoga
- Script detect karegi aur session save karegi
- Session saved in `.sessions/twitter/`
- **Next time login ki zaroorat nahi**

### Step 4: Test Tweet

```bash
uv run python src/playwright/twitter_bot.py post "Your tweet text here"
```

### Step 5: MCP Server (Claude Code Integration)

MCP server registered in `.mcp.json`:
```json
"fte-twitter": {
  "type": "stdio",
  "command": "uv",
  "args": ["run", "python", "src/mcp/twitter_server.py"]
}
```

After setup, Claude Code mein bolo:
> "Tweet karo: Hello World!"

---

## Files Created

| File | Purpose |
|------|---------|
| `src/playwright/twitter_bot.py` | Twitter browser automation bot |
| `src/mcp/twitter_server.py` | MCP server for Claude Code integration |
| `.sessions/twitter/` | Browser session data (login persistence) |

---

## Problems & Solutions

### Problem 1: Twitter API — 402 Payment Required
**Error:** `402 Payment Required — Your enrolled account does not have any credits to fulfill this request.`
**Cause:** Twitter Pay-Per-Use plan requires credits. $0 balance means no API access.
**Solution:** Use Playwright instead of API. Or buy minimum $5 credits on developer.x.com > Billing > Credits.

### Problem 2: "Couldn't sign you in — This browser or app may not be secure"
**Error:** Google OAuth popup blocks login in Playwright browser
**Cause:** Google detects Playwright's Chromium as automated browser and refuses OAuth
**Solution:** **DO NOT use "Sign in with Google"**. Use Twitter's own email/username + password login. Or use "Sign up" flow to link email first.

### Problem 3: Email entered but no password page — "Could not log you in now"
**Error:** After entering email on Twitter login page, error appears instead of password prompt
**Cause:** Twitter's aggressive bot detection blocks login flow in automated browsers
**Solution:** Use "Sign up" approach — enter email in sign up flow, Twitter detects existing account and redirects to login. This bypasses the direct login bot detection.

### Problem 4: Playwright Chromium not found
**Error:** `Executable doesn't exist at /home/.../.cache/ms-playwright/chromium-1208`
**Cause:** Default `playwright install` needs sudo on WSL
**Solution:** Install locally:
```bash
PLAYWRIGHT_BROWSERS_PATH=0 uv run playwright install chromium
```

### Problem 5: Windows Chrome — remote debugging pipe error
**Error:** `Remote debugging pipe file descriptors are not open` (exit code 13)
**Cause:** Windows Chrome executable cannot run with Playwright's remote debugging from WSL
**Solution:** Use Playwright's own Chromium, not Windows Chrome. Remove `executable_path` and `channel` options.

### Problem 6: Firefox path not found
**Error:** `Executable doesn't exist at /home/.../.cache/ms-playwright/firefox-1509`
**Cause:** Firefox installed with `PLAYWRIGHT_BROWSERS_PATH=0` (local) but code looks in global cache
**Solution:** Stay with Chromium (same as WhatsApp watcher). Firefox not needed — Chromium + Stealth works fine.

### Problem 7: Login detection not working — "Still waiting..."
**Error:** Script keeps saying "Still waiting..." even after successful login
**Cause:** `is_logged_in()` using DOM selectors that don't match current Twitter UI
**Solution:** URL-based detection:
```python
# Check if URL contains /home (means logged in)
if "/home" in current_url:
    return True
```

### Problem 8: Twitter Developer Console — no Free tier option
**Error:** No "Free" or "Downgrade" option in developer.x.com
**Cause:** New accounts (Feb 2026+) default to Pay-Per-Use. Free tier no longer available for new developers.
**Solution:** Either buy $5 credits or use Playwright (free).

### Problem 9: Twitter auth setup — "Not a valid URL format"
**Error:** Optional URL fields in Twitter app settings can't be left empty
**Cause:** Twitter requires valid URL format even for optional fields
**Solution:** Use `https://example.com` for Callback URL and Website URL.

---

## Key Technical Details

### Browser Launch (Anti-Detection Config)
```python
self._context = self._playwright.chromium.launch_persistent_context(
    user_data_dir=str(self._session_path),
    headless=self._headless,
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-infobars",
        "--disable-dev-shm-usage",
        "--no-first-run",
    ],
    ignore_default_args=["--enable-automation"],
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
)
stealth = Stealth()
stealth.apply_stealth_sync(self._context)
```

**Key difference from LinkedIn/WhatsApp:**
- `ignore_default_args=["--enable-automation"]` — removes automation flag
- Custom `user_agent` — mimics real Chrome
- These extra flags needed because Twitter has stricter bot detection than LinkedIn

### Twitter Post Flow (DOM Selectors)
```
1. Navigate to: https://x.com/compose/post
2. Find compose box: div[data-testid="tweetTextarea_0"]
3. Type text with delay=30ms per character
4. Find Post button: button[data-testid="tweetButton"]
5. Click Post → wait 3 seconds
```

### Twitter Developer App Details
- App Name: 20288916236027453344Shahzainali
- App ID: 32509232
- Plan: Pay Per Use
- Credits: $0.00 (not purchased)
- Twitter Handle: @Shahzainali604
- User Auth: Read and Write + Web App

---

## Testing Checklist

- [x] `uv run python src/playwright/twitter_bot.py login` — session saved (via sign up flow)
- [x] `uv run python src/playwright/twitter_bot.py post "test"` — tweet posted
- [ ] Reply to tweet — needs testing
- [ ] Like a tweet — needs testing
- [ ] MCP server via Claude Code — needs testing
- [ ] Headless mode — needs testing

---

## Twitter vs LinkedIn Playwright Comparison

| Feature | Twitter/X | LinkedIn |
|---------|-----------|----------|
| Bot Detection | Very strict | Moderate |
| Login Method | Sign up flow (workaround) | Direct email + password |
| Extra Anti-Detection | `ignore_default_args`, custom user_agent | Standard Stealth only |
| Post Selector | `data-testid="tweetTextarea_0"` | `div.ql-editor` (Quill) |
| Post Button | `data-testid="tweetButton"` | `share-actions__primary-action` |
| Compose URL | `x.com/compose/post` | Feed page modal |
