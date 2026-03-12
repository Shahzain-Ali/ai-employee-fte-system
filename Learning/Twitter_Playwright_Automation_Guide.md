# Twitter/X Automation — Playwright Setup Guide

**Date:** 2026-03-04 (Updated: 2026-03-05)
**Author:** Shahzain Bangash + Claude Opus 4.6
**Status:** WORKING — Tweet post via MCP server (headless Firefox) tested successfully
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
| Post Tweet | WORKING (MCP + headless) |
| Reply to Tweet | Built (needs testing) |
| Like a Tweet | Built (needs testing) |
| Get My Tweets | Built (headless scraping unreliable) |
| Login Session Persistence | WORKING (Chromium login → cookie export → Firefox headless) |
| MCP Server Integration | WORKING |

---

## Architecture: Dual Browser Approach

Twitter/X headless Chromium ko block karta hai (blank page dikhata hai). Isliye hum **dual browser** approach use karte hain:

```
LOGIN (one-time):
  Chromium (non-headless, visible) → User manually logs in → Cookies exported to JSON

MCP OPERATIONS (automated, headless):
  Firefox (headless) → Cookies injected from JSON → Tweet/Reply/Like
```

### Why This Works
- **Chromium headless** → X.com detects aur blank page dikhata hai (title empty, no DOM)
- **Firefox headless** → X.com allow karta hai, page properly load hota hai
- **Cookie injection** → Login ek baar Chromium mein, cookies file mein save, Firefox reuse karta hai

### Session Files
```
.sessions/twitter/          → Chromium session (login ke liye)
.sessions/twitter-ff2/      → Firefox session (MCP headless ke liye)
.sessions/twitter_cookies.json → Exported cookies (Chromium → Firefox bridge)
```

---

## Setup Steps

### Step 1: Install Dependencies

```bash
uv pip install playwright playwright-stealth
uv run playwright install chromium
uv run playwright install firefox
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
- Login karo (username + password ya "Sign in with Google")
- Login hone ke baad URL `x.com/home` pe redirect hoga
- Script detect karegi, **cookies auto-export** karegi, aur session save karegi
- **Next time login ki zaroorat nahi** (jab tak cookies expire na hon)

### Step 4: Test Tweet (Direct Script)

```bash
uv run python -c "
import asyncio
from src.playwright.twitter_bot import TwitterBot

async def test():
    bot = TwitterBot(headless=True)
    await bot.start()
    if await bot.is_logged_in():
        result = await bot.post_tweet('Your tweet text here')
        print(result)
    await bot.stop()

asyncio.run(test())
"
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
> "Post a tweet: Hello World!"

---

## Files Created

| File | Purpose |
|------|---------|
| `src/playwright/twitter_bot.py` | Twitter browser automation bot (async, dual-browser) |
| `src/mcp/twitter_server.py` | MCP server for Claude Code integration (async) |
| `.sessions/twitter/` | Chromium session data (login) |
| `.sessions/twitter-ff2/` | Firefox session data (headless operations) |
| `.sessions/twitter_cookies.json` | Exported cookies (bridge between browsers) |

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

### Problem 6: Login detection not working — "Still waiting..."
**Error:** Script keeps saying "Still waiting..." even after successful login
**Cause:** `is_logged_in()` using DOM selectors that don't match current Twitter UI
**Solution:** URL-based detection:
```python
if "/home" in current_url:
    return True
```

### Problem 7: Twitter Developer Console — no Free tier option
**Error:** No "Free" or "Downgrade" option in developer.x.com
**Cause:** New accounts (Feb 2026+) default to Pay-Per-Use. Free tier no longer available for new developers.
**Solution:** Either buy $5 credits or use Playwright (free).

### Problem 8: Twitter auth setup — "Not a valid URL format"
**Error:** Optional URL fields in Twitter app settings can't be left empty
**Cause:** Twitter requires valid URL format even for optional fields
**Solution:** Use `https://example.com` for Callback URL and Website URL.

### Problem 9: MCP Server — "Playwright Sync API inside asyncio loop"
**Error:** `Error: It looks like you are using Playwright Sync API inside the asyncio loop. Please use the Async API instead.`
**Cause:** FastMCP runs inside an async event loop, but bot was using `sync_playwright()` and synchronous methods.
**Solution:** Convert entire bot from sync to async:
```python
# BEFORE (broken with MCP):
from playwright.sync_api import sync_playwright
self._playwright = sync_playwright().start()
self._page.goto(url)

# AFTER (works with MCP):
from playwright.async_api import async_playwright
self._playwright = await async_playwright().start()
await self._page.goto(url)
```
All bot methods changed to `async def`, all Playwright calls prefixed with `await`.

### Problem 10: MCP Server — broken bot instance cached after login failure
**Error:** `'NoneType' object has no attribute 'goto'` on second MCP call
**Cause:** `_get_bot()` set global `_bot` before login check. If login failed, broken instance stayed cached.
**Solution:** Use local variable, only assign to global after successful login:
```python
async def _get_bot():
    global _bot
    if _bot is None:
        bot = TwitterBot(headless=True)  # local variable
        await bot.start()
        if not await bot.is_logged_in():
            await bot.stop()  # cleanup
            raise RuntimeError("Not logged in")
        _bot = bot  # only assign after success
    return _bot
```

### Problem 11: Headless Chromium — X.com shows blank page
**Error:** Page loads but title empty, no DOM elements, body text empty
**Cause:** Twitter/X aggressively detects headless Chromium and serves blank page. Extra stealth flags (`--disable-blink-features`, custom user-agent, `--headless=new`) all failed.
**Solution:** **Use Firefox headless instead.** Firefox headless is not detected by X.com:
```python
# Chromium headless → BLANK PAGE (blocked)
ctx = await pw.chromium.launch_persistent_context(headless=True, ...)
# Page: title="", body="", no elements

# Firefox headless → WORKS
ctx = await pw.firefox.launch_persistent_context(headless=True, ...)
# Page: title="X. It's what's happening / X", full DOM
```

### Problem 12: Firefox persistent context — session not preserved in headless
**Error:** Login done in Firefox non-headless, but headless Firefox shows "Sign up" page (not logged in)
**Cause:** Firefox persistent context doesn't reliably restore cookies between headless/non-headless sessions
**Solution:** **Cookie injection approach** — Login in Chromium (reliable session), export cookies to JSON, inject into Firefox headless:
```python
# Export from Chromium:
cookies = await chromium_context.cookies()
Path('cookies.json').write_text(json.dumps(cookies))

# Inject into Firefox:
cookies = json.loads(Path('cookies.json').read_text())
await firefox_context.add_cookies(filtered_cookies)
```

### Problem 13: Firefox non-headless crash in WSL
**Error:** `BrowserType.launch_persistent_context: Failed to launch the browser process.` (exit code 0)
**Cause:** Firefox non-headless needs a display server (X11/Wayland), WSL doesn't have one by default
**Solution:** Use Chromium for non-headless login (works in WSL), Firefox only for headless MCP operations. This is why we have the dual-browser architecture.

### Problem 14: `is_logged_in()` returns True on `about:blank`
**Error:** Bot reports logged in but page is at `about:blank` with no content
**Cause:** Old check: if URL doesn't contain `/login` → assume logged in. `about:blank` passes this check.
**Solution:** Navigate first, then check:
```python
async def is_logged_in(self):
    await self._page.goto("https://x.com", ...)
    await asyncio.sleep(5)
    # Check for "Sign in" link = NOT logged in
    sign_in = await self._page.query_selector('a[href="/login"]')
    if sign_in:
        return False
    # Check for /home redirect = logged in
    if "/home" in self._page.url:
        return True
```

### Problem 15: Post button click intercepted by overlay
**Error:** `ElementHandle.click: Timeout 30000ms exceeded — element is visible, enabled and stable — but another element intercepts click`
**Cause:** Cookie banner, notification popup, or "Subscribe to Premium" overlay covers the Post button
**Solution:** Use JavaScript `document.querySelector().click()` instead of Playwright click:
```python
# BEFORE (blocked by overlay):
await post_btn.click()

# AFTER (bypasses overlay):
await self._page.evaluate(
    'document.querySelector(\'button[data-testid="tweetButton"]\').click()'
)
```

### Problem 16: Tweet "posted successfully" but not appearing on profile
**Error:** Bot returns success, MCP returns success, but tweet not visible on X.com profile
**Cause:** `force=True` click was used which bypasses actionability checks — button was clicked but event didn't register properly
**Solution:** Combined fix:
1. Wait for button to be enabled before clicking
2. Use JavaScript click (reliable in Firefox)
3. Verify redirect away from `/compose` URL after click
```python
# Wait for enabled
for _ in range(10):
    if await post_btn.is_enabled():
        break
    await asyncio.sleep(0.5)

# JavaScript click
await self._page.evaluate('document.querySelector(...).click()')

# Verify
if "/compose" not in self._page.url:
    return {"status": "success", ...}
```

---

## Key Technical Details

### Dual-Browser Architecture
```python
# LOGIN MODE (headless=False) → Chromium
self._context = await self._playwright.chromium.launch_persistent_context(
    user_data_dir=str(self._chromium_session),
    headless=False,
    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", ...],
    ignore_default_args=["--enable-automation"],
    user_agent="Mozilla/5.0 ... Chrome/131.0.0.0 ...",
)
# After login → cookies exported to .sessions/twitter_cookies.json

# MCP MODE (headless=True) → Firefox
self._context = await self._playwright.firefox.launch_persistent_context(
    user_data_dir=str(self._firefox_session),
    headless=True,
    user_agent="Mozilla/5.0 ... Firefox/131.0",
    viewport={"width": 1920, "height": 1080},
)
# Cookies injected from .sessions/twitter_cookies.json
```

### Cookie Injection Flow
```python
# Filter only X.com cookies from exported file
x_cookies = [c for c in all_cookies
             if ".x.com" in c["domain"] or "twitter" in c["domain"]]

# Inject into Firefox context
await self._context.add_cookies(x_cookies)
```

### Twitter Post Flow (DOM Selectors)
```
1. Navigate to: https://x.com/home (dismiss overlays)
2. Navigate to: https://x.com/compose/post
3. Find compose box: div[data-testid="tweetTextarea_0"]
4. Type text with delay=30ms per character
5. Wait for Post button enabled: button[data-testid="tweetButton"]
6. JavaScript click: document.querySelector('button[data-testid="tweetButton"]').click()
7. Verify URL changed from /compose (confirms tweet sent)
```

### Twitter Developer App Details
- App Name: 20288916236027453344Shahzainali
- App ID: 32509232
- Plan: Pay Per Use
- Credits: $0.00 (not purchased)
- Twitter Handle: @ShahzainAl81729
- User Auth: Read and Write + Web App

---

## Testing Checklist

- [x] `uv run python src/playwright/twitter_bot.py login` — Chromium login + cookie export
- [x] Firefox headless login check — cookies injected, is_logged_in=True
- [x] Direct script tweet post (headless Firefox) — tweet posted and verified on X.com
- [x] MCP server `post_tweet` via Claude Code — tweet posted successfully
- [x] MCP server `get_my_tweets` — connected (returns empty due to headless scraping limits)
- [ ] Reply to tweet via MCP — needs testing
- [ ] Like a tweet via MCP — needs testing

---

## Twitter vs LinkedIn Playwright Comparison

| Feature | Twitter/X | LinkedIn |
|---------|-----------|----------|
| Bot Detection | Very strict (blocks headless Chromium) | Moderate (headless Chromium works) |
| Headless Browser | Firefox (Chromium blocked) | Chromium |
| Login Method | Chromium non-headless → cookie export | Chromium headless (session persists) |
| Cookie Bridge | Required (Chromium → JSON → Firefox) | Not needed |
| Extra Anti-Detection | Dual-browser, JS click, overlay dismiss | Standard Stealth only |
| Post Selector | `data-testid="tweetTextarea_0"` | `div.ql-editor` (Quill) |
| Post Button | `data-testid="tweetButton"` (JS click) | `share-actions__primary-action` |
| Compose URL | `x.com/compose/post` | Feed page modal |
| Async API | Required (MCP async loop) | Required (MCP async loop) |
