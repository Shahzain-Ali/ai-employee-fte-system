# Gold Tier — MCP Server Setup Guide (Facebook + Instagram)

**Date:** 2026-03-03
**Author:** Shahzain Bangash + Claude Opus 4.6
**Status:** FULLY WORKING — All MCP Servers Connected
**Prerequisite:** Meta_API_Facebook_Instagram_Setup_Guide.md must be completed first

---

## Overview

Ye guide batati hai ke kaise **MCP (Model Context Protocol) servers** setup karke Claude Code ko Facebook aur Instagram ke tools de sakte hain. Iske baad tum Claude Code mein sirf bol ke post/comment/reply kar sakte ho — manually Graph API Explorer kholne ki zaroorat nahi.

### Kya Hoga Iske Baad?

```
PEHLE (Manual):
  Tum → Graph API Explorer → Token paste → URL type → Submit → Post

AB (MCP):
  Tum → Claude Code mein bolo "Post this on Facebook" → Done!
```

### MCP Servers Jo Humne Setup Kiye:

| Server | Tools | Platform |
|---|---|---|
| `fte-facebook` | 5 tools | Facebook Page |
| `fte-instagram` | 6 tools | Instagram Creator Account |
| `fte-email` | 2 tools | Gmail |
| `fte-odoo` | 6 tools | Odoo Accounting |

---

## Prerequisites

Ye sab pehle se complete hona chahiye (Meta_API_Facebook_Instagram_Setup_Guide.md follow karo):

```
✅ Facebook Page created (e.g., "Agentive Solutions")
✅ Instagram Creator Account banaya
✅ Instagram Facebook Page se connected
✅ Meta Developer App created ("FTE Social Manager")
✅ Business Portfolio se App connected
✅ Long-Lived Tokens generated
✅ Graph API Explorer se Post/Comment/Reply test kiya
```

---

## Phase 1: .env File Setup

### 1.1 — Tokens .env Mein Save Karo

`.env` file mein ye values honi chahiye:

```env
# ===== FACEBOOK =====
FB_PAGE_ID=YOUR_PAGE_ID
FB_PAGE_ACCESS_TOKEN=YOUR_NEVER_EXPIRING_PAGE_TOKEN

# ===== INSTAGRAM =====
IG_USER_ID=YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID
IG_ACCESS_TOKEN=YOUR_60_DAY_USER_TOKEN

# ===== META API =====
META_APP_ID=YOUR_APP_ID
META_API_VERSION=v25.0
META_BUSINESS_PORTFOLIO_ID=YOUR_BUSINESS_PORTFOLIO_ID
```

### 1.2 — IDs Kahan Se Milenge?

| Variable | Kahan Se Milegi | Kaise Milegi |
|---|---|---|
| `FB_PAGE_ID` | Business Portfolio → Pages | Business Settings mein Page ID (URL bar wali ID NAHI!) |
| `FB_PAGE_ACCESS_TOKEN` | Graph API Explorer | Long-lived User Token se Page token nikalo (Meta Guide Phase 10) |
| `IG_USER_ID` | Graph API Explorer | `{page_id}?fields=instagram_business_account` se milega |
| `IG_ACCESS_TOKEN` | Browser URL | Short-lived token ko 60-day token mein convert karo (Meta Guide Phase 10) |
| `META_APP_ID` | Developer Dashboard | Settings → Basic → App ID |
| `META_API_VERSION` | Fixed value | `v25.0` (March 2026) |
| `META_BUSINESS_PORTFOLIO_ID` | Business Settings | URL bar mein ya Business Info mein |

### CRITICAL — Page ID Ka Confusion

Facebook mein **do different Page IDs** hoti hain:

| ID Type | Example | Kahan Dikhti Hai | API Mein Kaam Karegi? |
|---|---|---|---|
| URL ID (New Pages Experience) | `61585031032595` | `facebook.com/profile.php?id=61585031032595` | **NAHI** |
| Business Portfolio ID | `1044367502088758` | `business.facebook.com/settings/` → Pages | **HAAN** |

**Hamesha Business Portfolio Page ID use karo!**

Kaise dhundein:
1. Jao: `business.facebook.com/settings/`
2. Left side: **Accounts** → **Pages**
3. Apna Page click karo
4. ID wahan likhi hogi (e.g., `ID: 1044367502088758`)

---

## Phase 2: MCP Server Files (Pehle Se Bane Hue Hain)

### Project Structure:

```
src/mcp/
├── _meta_client.py      ← Shared HTTP client (retry, rate limit, error handling)
├── facebook_server.py   ← Facebook MCP server (5 tools)
├── instagram_server.py  ← Instagram MCP server (6 tools)
├── odoo_server.py       ← Odoo MCP server (6 tools)
├── index.js             ← Email MCP server (Node.js, 2 tools)
├── package.json         ← Node.js dependencies
└── node_modules/        ← Node.js packages
```

### 2.1 — _meta_client.py (Shared Client)

Ye dono servers (Facebook + Instagram) ka backbone hai:

| Feature | Description |
|---|---|
| **Retry logic** | 3 retries with exponential backoff (1s, 2s, 4s) |
| **Rate limiting** | X-App-Usage header se detect karta hai |
| **Token expiry** | Code 190 detect karke clear error message deta hai |
| **Permission errors** | Code 10, 200 detect karta hai |
| **Base URL** | `https://graph.facebook.com/{api_version}` |

### 2.2 — facebook_server.py (5 Tools)

| Tool Name | Kya Karta Hai | Parameters |
|---|---|---|
| `create_page_post` | Facebook Page pe post karta hai | `message`, `link` (optional) |
| `get_page_posts` | Recent posts ki list deta hai | `limit` (default 10) |
| `get_post_comments` | Kisi post ke comments deta hai | `post_id`, `limit` (default 25) |
| `reply_to_comment` | Comment ka reply karta hai | `comment_id`, `message` |
| `get_page_insights` | Page analytics deta hai | `period` (day/week/days_28) |

**Token Used:** `FB_PAGE_ACCESS_TOKEN` (Never-expiring Page Token)

### 2.3 — instagram_server.py (6 Tools)

| Tool Name | Kya Karta Hai | Parameters |
|---|---|---|
| `create_ig_post` | Instagram pe image post karta hai (2-step) | `image_url`, `caption` |
| `create_ig_reel` | Instagram pe reel post karta hai (2-step) | `video_url`, `caption` |
| `get_ig_media` | Recent posts ki list deta hai | `limit` (default 10) |
| `get_ig_comments` | Kisi post ke comments deta hai | `media_id`, `limit` (default 25) |
| `reply_ig_comment` | Comment ka reply karta hai | `comment_id`, `message` |
| `get_ig_insights` | Account analytics deta hai | `period` (day/week/days_28) |

**Token Used:** `IG_ACCESS_TOKEN` (60-day User Token)

### Instagram 2-Step Posting Flow:

```
Step 1: Media Container banao (image/video upload)
  → POST /{ig_user_id}/media + image_url + caption
  → Container ID milta hai

Step 2: Wait for processing (automatic polling)
  → GET /{container_id}?fields=status_code
  → FINISHED hone tak wait karo

Step 3: Publish karo
  → POST /{ig_user_id}/media_publish + creation_id
  → Media ID milta hai = Post live!
```

---

## Phase 3: .mcp.json — MCP Server Registration

### 3.1 — Configuration File

Claude Code ko batana padta hai ke kaunse MCP servers available hain. Ye `.mcp.json` file project root mein hoti hai:

```json
{
  "mcpServers": {
    "fte-email": {
      "type": "stdio",
      "command": "node",
      "args": [
        "/mnt/e/hackathon-0/full-time-equivalent-project/src/mcp/index.js"
      ],
      "env": {}
    },
    "fte-odoo": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "python",
        "src/mcp/odoo_server.py"
      ],
      "env": {}
    },
    "fte-facebook": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "python",
        "src/mcp/facebook_server.py"
      ],
      "env": {}
    },
    "fte-instagram": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "python",
        "src/mcp/instagram_server.py"
      ],
      "env": {}
    }
  }
}
```

### CRITICAL — `uv run python` vs `python`

| Command | Kaam Karega? | Kyun? |
|---|---|---|
| `"command": "python"` | **NAHI** | `python` command nahi hoti WSL/Linux pe, sirf `python3` hota hai. Aur dependencies (dotenv, mcp, requests) installed nahi hoti |
| `"command": "python3"` | **SHAYAD NAHI** | Dependencies missing hongi agar globally installed nahi |
| `"command": "uv"` with args `["run", "python", ...]` | **HAAN** | `uv` project ki virtual environment aur dependencies automatically manage karta hai |

**Hamesha `uv run python` use karo MCP servers ke liye!**

### 3.2 — Email Server (Node.js) Kyun Different Hai?

Email server Node.js mein hai (`index.js`), baaki sab Python mein. Isliye:
- Email: `"command": "node"` + full path to `index.js`
- Python servers: `"command": "uv"` + `["run", "python", "relative/path.py"]`

---

## Phase 4: Dependencies Setup

### 4.1 — Python Dependencies (pyproject.toml)

Ye packages zaroori hain:

```toml
[project]
dependencies = [
    "python-dotenv>=1.0.0",    # .env file loading
    "mcp[cli]>=1.26.0",        # MCP server framework
    "requests>=2.31.0",         # HTTP client for Meta API
]
```

### 4.2 — Install Karo

```bash
uv sync
```

Ye sab dependencies install kar dega `pyproject.toml` se.

### 4.3 — Verify Karo

```bash
uv run python -c "from dotenv import load_dotenv; print('dotenv OK')"
uv run python -c "from mcp.server.fastmcp import FastMCP; print('FastMCP OK')"
uv run python -c "import requests; print('requests OK')"
```

Teeno mein "OK" aana chahiye.

---

## Phase 5: MCP Servers Test Karna

### 5.1 — Tokens Loading Test

```bash
uv run python -c "
from dotenv import load_dotenv
load_dotenv()
import os
print('FB_PAGE_ID:', os.getenv('FB_PAGE_ID'))
print('IG_USER_ID:', os.getenv('IG_USER_ID'))
print('META_API_VERSION:', os.getenv('META_API_VERSION'))
print('FB_TOKEN set:', bool(os.getenv('FB_PAGE_ACCESS_TOKEN')))
print('IG_TOKEN set:', bool(os.getenv('IG_ACCESS_TOKEN')))
"
```

**Expected Output:**
```
FB_PAGE_ID: 1044367502088758
IG_USER_ID: 17841477106514810
META_API_VERSION: v25.0
FB_TOKEN set: True
IG_TOKEN set: True
```

### 5.2 — Facebook API Test

```bash
uv run python -c "
from dotenv import load_dotenv
load_dotenv()
import os
from src.mcp._meta_client import MetaGraphClient

fb_token = os.getenv('FB_PAGE_ACCESS_TOKEN')
fb_page_id = os.getenv('FB_PAGE_ID')
version = os.getenv('META_API_VERSION', 'v25.0')

client = MetaGraphClient(access_token=fb_token, api_version=version)
result = client.get(f'/{fb_page_id}', {'fields': 'id,name'})
print('Facebook Page:', result)
"
```

**Expected Output:**
```
Facebook Page: {'id': '1044367502088758', 'name': 'Agentive Solutions'}
```

### 5.3 — Instagram API Test

```bash
uv run python -c "
from dotenv import load_dotenv
load_dotenv()
import os
from src.mcp._meta_client import MetaGraphClient

ig_token = os.getenv('IG_ACCESS_TOKEN')
ig_user_id = os.getenv('IG_USER_ID')
version = os.getenv('META_API_VERSION', 'v25.0')

client = MetaGraphClient(access_token=ig_token, api_version=version)
result = client.get(f'/{ig_user_id}', {'fields': 'id,username,name'})
print('Instagram:', result)
"
```

**Expected Output:**
```
Instagram: {'id': '17841477106514810', 'username': 'shahzain_ali5512', 'name': 'Shahzain Ali Bangash'}
```

### 5.4 — Claude Code MCP Connection Test

```bash
claude --model sonnet
```

**Expected Output:**
```
Project MCPs
  fte-email      · connected
  fte-facebook   · connected
  fte-instagram  · connected
  fte-odoo       · connected
```

Agar sab connected dikhe toh **sab kuch kaam kar raha hai!**

---

## Phase 6: Claude Code Se Use Karna

### Facebook Commands:

Ye prompts Claude Code mein type karo:

**Post karo:**
```
Post on Facebook Page: "Hello from AI Employee! This is an automated post."
```

**Recent posts dekho:**
```
Show me the latest 5 posts from my Facebook Page
```

**Comments dekho:**
```
Get all comments on my latest Facebook post
```

**Comment ka reply do:**
```
Reply to the latest comment on my Facebook post with "Thank you for your feedback!"
```

### Instagram Commands:

**Image post karo:**
```
Post this image on Instagram with caption "Beautiful sunset! #nature #photography": https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg
```

**Recent posts dekho:**
```
Show me my latest Instagram posts
```

**Comments dekho:**
```
Get comments on my latest Instagram post
```

**Comment reply do:**
```
Reply to the latest comment on my Instagram post with "Thanks! Glad you liked it"
```

---

## Problems & Solutions — MCP Server Specific

### Problem 1: MCP Server "failed" on startup

```
fte-facebook · failed
fte-instagram · failed
fte-odoo · failed
```

**Cause:** `.mcp.json` mein `"command": "python"` tha lekin system pe `python` command nahi hai (WSL/Linux pe `python3` hota hai). Aur dependencies bhi missing hoti hain.

**Solution:** `.mcp.json` mein command change karo:

```json
WRONG:  "command": "python",  "args": ["src/mcp/facebook_server.py"]
RIGHT:  "command": "uv",      "args": ["run", "python", "src/mcp/facebook_server.py"]
```

### Problem 2: Settings.json Hook Format Error

```
Settings Error
hooks → Stop → 0 → hooks: Expected array, but received undefined
Hooks use a new format with matchers.
```

**Cause:** `.claude/settings.json` mein purana hook format tha.

**Old (WRONG) format:**
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "command": "./scripts/ralph-wiggum-check.sh"
      }
    ]
  }
}
```

**New (CORRECT) format:**
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/ralph-wiggum-check.sh"
          }
        ]
      }
    ]
  }
}
```

### Problem 3: "ModuleNotFoundError: No module named 'dotenv'"

**Cause:** Python dependencies installed nahi hain.

**Solution:**
```bash
uv sync
```

### Problem 4: "FB_PAGE_ACCESS_TOKEN not set in environment"

**Cause:** `.env` file mein token nahi hai ya placeholder hai.

**Solution:** Meta_API_Facebook_Instagram_Setup_Guide.md ka Phase 10 follow karo — Long-lived tokens generate karke `.env` mein paste karo.

### Problem 5: Meta API token expired (OAuthException code 190)

**Cause:** Token expire ho gaya.

**Solution:**
- **FB_PAGE_ACCESS_TOKEN** — Ye never-expiring hona chahiye. Agar expire hua toh dobara Long-Lived User Token se Page Token nikalo.
- **IG_ACCESS_TOKEN** — 60 din mein expire hota hai. Har 50 din mein renew karo (Meta Guide Phase 10, Step 2).

### Problem 6: "Only photo or video can be accepted" (Instagram Post)

**Cause:** Image URL valid public URL nahi hai, ya redirect hota hai.

**Solution:**
- Direct image URL use karo (`.jpg`, `.png` extension wali)
- URL publicly accessible hona chahiye (no login required)
- Redirect URLs kaam nahi karti — final URL chahiye
- Test karo: browser mein URL open karo, image directly dikhni chahiye

### Problem 7: Instagram `create_ig_post` timeout

**Cause:** Image processing mein 60 seconds se zyada lag raha hai.

**Solution:** Image size check karo:
- Maximum: 8MB
- Recommended: 1080x1080 pixels
- Formats: JPEG, PNG

### Problem 8: API version mismatch

**Cause:** Code mein `v21.0` default tha lekin latest `v25.0` hai.

**Solution:** `.env` mein `META_API_VERSION=v25.0` set karo. Code automatically `.env` se version pick karega.

---

## Token Management — Quick Reference

### Kaunsa Token Kiske Liye:

| .env Variable | Token Type | Expiry | Platform |
|---|---|---|---|
| `FB_PAGE_ACCESS_TOKEN` | Page Token | **Never** | Facebook Page (post, comment, reply) |
| `IG_ACCESS_TOKEN` | User Token | **60 days** | Instagram (post, comment, reply) |

### Token Renewal Schedule:

| Token | Action | Frequency |
|---|---|---|
| `FB_PAGE_ACCESS_TOKEN` | Kuch nahi karna | Never expires |
| `IG_ACCESS_TOKEN` | Meta Guide Phase 10, Step 2 follow karo | Har 50 din |

### Renewal Process (IG_ACCESS_TOKEN):

1. Graph API Explorer → Generate fresh short-lived User Token
2. Browser mein exchange URL open karo (App Secret + short-lived token)
3. 60-day token milega → `.env` mein paste karo
4. Claude Code restart karo

---

## Architecture — How MCP Servers Work

```
┌──────────────┐
│  User types  │
│  prompt in   │
│  Claude Code │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Claude AI   │────▶│  MCP Server      │────▶│  Meta Graph  │
│  decides     │     │  (Python/uv)     │     │  API         │
│  which tool  │     │                  │     │              │
│  to use      │◀────│  Returns result  │◀────│  Facebook/   │
│              │     │  to Claude       │     │  Instagram   │
└──────────────┘     └──────────────────┘     └──────────────┘

MCP Server internally:
  1. Reads token from .env
  2. Creates MetaGraphClient
  3. Makes HTTP request to graph.facebook.com
  4. Handles errors, retries, rate limits
  5. Returns result string to Claude
```

### Communication Flow:

```
Claude Code ──stdio──▶ MCP Server (uv run python facebook_server.py)
                           │
                           ├── Reads .env (tokens, IDs)
                           ├── Creates MetaGraphClient
                           ├── HTTP GET/POST to Meta Graph API
                           ├── Handles errors
                           └── Returns result via stdio
```

---

## File Reference — What Each File Does

| File | Purpose | Language |
|---|---|---|
| `.mcp.json` | Registers MCP servers with Claude Code | JSON config |
| `.env` | Stores tokens, IDs, secrets (NEVER commit!) | Environment |
| `.gitignore` | Ensures .env is not committed | Git config |
| `.claude/settings.json` | Claude Code hooks and settings | JSON config |
| `src/mcp/_meta_client.py` | Shared HTTP client for Meta API | Python |
| `src/mcp/facebook_server.py` | Facebook MCP server (5 tools) | Python |
| `src/mcp/instagram_server.py` | Instagram MCP server (6 tools) | Python |
| `src/mcp/odoo_server.py` | Odoo accounting MCP server | Python |
| `src/mcp/index.js` | Email MCP server | Node.js |
| `src/utils/retry.py` | Retry decorator with exponential backoff | Python |
| `pyproject.toml` | Python dependencies | TOML config |

---

## Checklist — Sab Kuch Verify Karo

```
SETUP:
  [ ] .env mein FB_PAGE_ID set hai (Business Portfolio ID, URL ID nahi)
  [ ] .env mein FB_PAGE_ACCESS_TOKEN set hai (never-expiring Page Token)
  [ ] .env mein IG_USER_ID set hai (Instagram Business Account ID)
  [ ] .env mein IG_ACCESS_TOKEN set hai (60-day User Token)
  [ ] .env mein META_API_VERSION=v25.0 set hai
  [ ] .mcp.json mein "uv" command hai (not "python")
  [ ] .claude/settings.json mein new hook format hai
  [ ] uv sync successfully run hua (dependencies installed)

TESTING:
  [ ] uv run python -c "from dotenv import load_dotenv..." — tokens loading
  [ ] Facebook API test — Page name aata hai
  [ ] Instagram API test — username aata hai
  [ ] Claude Code start — sab MCP servers "connected"
  [ ] Claude Code se Facebook post test
  [ ] Claude Code se Instagram post test

COMMON MISTAKES TO AVOID:
  [ ] URL wali Page ID use nahi ki (61585... NAHI, 10443... HAAN)
  [ ] .mcp.json mein "python" ki jagah "uv" + "run" + "python" likha
  [ ] .env file .gitignore mein hai (tokens leak nahi honge)
  [ ] App Mode "Development" pe hai (production ke liye App Review chahiye)
  [ ] Instagram product app mein add kiya hai ("Add Product" → "Instagram")
  [ ] Instagram Tester role accept kiya hai
```

---

## Troubleshooting Decision Tree

```
MCP Server "failed"?
  ├── Check: .mcp.json mein "uv" command hai? → Fix it
  ├── Check: uv sync hua hai? → Run uv sync
  └── Check: .env mein tokens hain? → Add tokens

Facebook post error?
  ├── "(#200) permission" → Page Token use karo, User Token nahi
  ├── "token expired" → Never-expiring Page Token generate karo (Meta Guide Phase 10)
  ├── "Object does not exist" → Business Portfolio Page ID use karo
  └── "rate limit" → 1-2 minute wait karo

Instagram post error?
  ├── "Only photo or video" → Direct public image URL use karo, parameters separately add karo
  ├── "container processing failed" → Image size < 8MB check karo
  ├── "instagram_business_account missing" → Instagram permissions add karo + Instagram product add karo
  └── "token expired" → 60-day token renew karo (Meta Guide Phase 10, Step 2)

Claude Code start pe error?
  ├── "Settings Error hooks" → .claude/settings.json ka format fix karo
  └── "No such file" → File paths check karo .mcp.json mein
```

---

## Next Steps After MCP Setup

1. **Twitter API Setup** — Free tier (1500 posts/month) + Playwright for replies
2. **LinkedIn API Setup** — Apply for API access + Playwright fallback
3. **Cross-Domain Workflows** — Email aaye → Invoice banao → Social pe post karo
4. **Scheduled Posts** — APScheduler se automated posting
5. **Comment Monitoring** — Automatically detect aur reply karo
