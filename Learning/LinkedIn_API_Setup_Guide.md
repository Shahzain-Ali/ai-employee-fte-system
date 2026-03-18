# LinkedIn Official API — Complete Setup Guide

**Date:** 2026-03-18
**Author:** Shahzain Bangash + Claude Opus 4.6
**Status:** FULLY WORKING — Post on LinkedIn via Official API

---

## Overview

Ye guide step-by-step batati hai ke kaise LinkedIn Official API setup karke automated posting ki ja sakti hai. Pehle hum Playwright (browser automation) use karte the, ab Official API use karte hain jo zyada reliable aur safe hai.

### API vs Playwright — Kyun Switch Kiya?

| Feature | Playwright (Old) | Official API (New) |
|---|---|---|
| Reliability | Browser updates se break hota | Stable, versioned API |
| Speed | Slow (browser open karna padta) | Fast (direct HTTP calls) |
| Detection Risk | LinkedIn ban kar sakta | Officially allowed |
| Rate Limits | Unknown | Clear documentation |
| Setup | Complex (stealth, cookies) | Simple (token based) |

### Kya Kya Automate Ho Sakta Hai?

| Action | Supported | Endpoint |
|---|---|---|
| Create Text Post | YES | `/v2/ugcPosts` |
| Create Post with Image | YES | `/v2/ugcPosts` + `/v2/assets` |
| Get Profile Info | YES | `/v2/userinfo` |
| Get Posts | YES | `/v2/ugcPosts` |
| Comment on Post | YES | `/v2/socialActions` |
| Like a Post | YES | `/v2/socialActions` |

### Important Limitations
- **Personal profile pe post karne ke liye Person URN chahiye** — Organization URN se 403 error aata hai agar page admin permissions nahi hain
- **Access Token 60 days mein expire hota hai** — refresh karna padta hai
- **Free tier mein limited API calls** — but normal use ke liye kaafi hai

---

## Prerequisites (Ye Pehle Se Hona Chahiye)

1. LinkedIn personal account (login ke liye)
2. LinkedIn Company Page (optional — agar page pe post karna ho)

---

## Step 1: LinkedIn Page Create Karna

> **Note:** Agar sirf personal profile pe post karna hai toh page banana zaroori nahi, lekin business ke liye recommended hai.

1. LinkedIn open karo: `https://www.linkedin.com`
2. Top bar mein **"For Business"** dropdown pe click karo
3. **"Create a Company Page"** select karo
4. Page type select karo:
   - **Small business** — agar startup ya chhoti company hai
   - **Medium to large business** — badi company ke liye
   - **Showcase page** — sub-brand ke liye
   - **Educational institution** — school/university ke liye

### Page Details Fill Karo:

| Field | Example Value | Notes |
|---|---|---|
| **Name** | Agentive Solutions | Company ka naam |
| **LinkedIn public URL** | agentive-solutions | Auto-generate hota hai, customize kar sakte ho |
| **Website** | https://agentive.solutions | Optional |
| **Industry** | Technology, Information and Internet | Dropdown se select karo |
| **Organization size** | 2-10 employees | Ya "0-1" agar solo ho |
| **Organization type** | Sole Proprietorship | Solo founder ke liye best option |
| **Tagline** | AI-Powered Automation Solutions for Businesses | Short description |
| **Logo** | Upload company logo | 300x300 recommended |

5. Checkbox tick karo: "I verify that I am an authorized representative..."
6. **"Create page"** click karo

✅ **Page ban gaya!**

---

## Step 2: LinkedIn Developer App Create Karna

1. LinkedIn Developer Portal kholein: `https://developer.linkedin.com/`
2. **"Create app"** button pe click karo (top right)
3. App details fill karo:

| Field | Value | Notes |
|---|---|---|
| **App name** | Agentive Solutions App | Koi bhi descriptive naam |
| **LinkedIn Page** | Agentive Solutions | Step 1 mein banayi gayi page select karo |
| **Privacy policy URL** | https://agentive.solutions/privacy | Optional for development |
| **App logo** | Upload logo | Required — 100x100 minimum |

4. **"Create app"** click karo

✅ **Developer App ban gayi!**

---

## Step 3: App Permissions (Products) Enable Karna

1. App settings mein **"Products"** tab pe jao
2. In products ko **Request access** karo:

| Product | Purpose | Approval |
|---|---|---|
| **Share on LinkedIn** | Posts create karna | Instant approval |
| **Sign In with LinkedIn using OpenID Connect** | Profile info access | Instant approval |
| **Community Management API** | Comments, likes | May need review |

3. Har product ke Terms accept karo
4. Wait karo — kuch instantly approve ho jate hain, kuch mein 1-2 din lag sakte hain

### Verify Permissions (OAuth 2.0 Scopes):

**"Auth"** tab mein check karo ke ye scopes available hain:

| Scope | Purpose |
|---|---|
| `openid` | Sign in with LinkedIn |
| `profile` | Basic profile info |
| `email` | Email address |
| `w_member_social` | Create posts on personal profile |

> ⚠️ **`w_member_social`** sabse important hai — iske bina post nahi hoga!

---

## Step 4: Organization URN (Page ID) Find Karna

1. Apni LinkedIn Company Page open karo browser mein
2. `Ctrl+U` press karo (View Page Source)
3. `Ctrl+F` press karo aur search karo: `urn:li:organization:`
4. Number copy karo — ye tumhara Organization URN hai

**Example:**
```
urn:li:organization:112495928
```

> **Alternative Method:** Page URL se bhi mil sakta hai
> `https://www.linkedin.com/company/112495928/`

---

## Step 5: Person URN Find Karna

Person URN tumhara personal LinkedIn ID hai. Ye access token milne ke baad API se milta hai.

### Method: API Se (Recommended)

Token milne ke baad (Step 7), ye API call karo:

```bash
curl -s "https://api.linkedin.com/v2/userinfo" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | python -m json.tool
```

Response mein `sub` field tumhara Person URN hai:
```json
{
    "sub": "abc123def456",
    "name": "Shahzain Ali",
    "email": "your@email.com"
}
```

Person URN hoga: `urn:li:person:abc123def456`

---

## Step 6: Client Credentials Note Karna

**"Auth"** tab mein ye values hain:

| Credential | Where to Find |
|---|---|
| **Client ID** | Auth tab → Client ID |
| **Client Secret** | Auth tab → Client Secret (click eye icon) |

> ⚠️ **NEVER share Client Secret publicly!**

### Redirect URLs Configure Karo:

**"Auth"** tab mein **"Authorized redirect URLs for your app"** section mein add karo:

```
http://localhost:8080/callback
https://www.linkedin.com/developers/tools/oauth/redirect
```

---

## Step 7: Access Token Generate Karna (OAuth 2.0)

### Method A: LinkedIn Developer Tools (Easiest — Recommended for Testing)

1. Jao: `https://www.linkedin.com/developers/tools/oauth`
2. Apni app select karo
3. **Scopes** mein select karo:
   - ✅ `openid`
   - ✅ `profile`
   - ✅ `email`
   - ✅ `w_member_social`
4. **"Request access token"** click karo
5. LinkedIn login karo aur **"Allow"** click karo
6. **Access Token** copy karo

> ⚠️ **Token 60 days mein expire hota hai!** Calendar mein reminder lagao.

### Method B: Manual OAuth Flow (For Production)

**Step 7B-1: Authorization Code Get Karo**

Browser mein ye URL open karo (apni values replace karo):

```
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080/callback&scope=openid%20profile%20email%20w_member_social
```

Allow karne ke baad redirect hoga:
```
http://localhost:8080/callback?code=AUTHORIZATION_CODE_HERE
```

`code` parameter copy karo.

**Step 7B-2: Authorization Code ko Access Token mein Exchange Karo**

```bash
curl -X POST "https://www.linkedin.com/oauth/v2/accessToken" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE_HERE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=http://localhost:8080/callback"
```

Response:
```json
{
    "access_token": "AQV...",
    "expires_in": 5184000
}
```

`5184000` seconds = **60 days**

---

## Step 8: Environment Variables Set Karna

`.env` file mein ye variables add karo:

```env
# LinkedIn API Configuration
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_PERSON_URN=urn:li:person:your_person_id_here
LINKEDIN_ORGANIZATION_URN=urn:li:organization:your_org_id_here
```

> ⚠️ **NEVER commit `.env` to git!** Already `.gitignore` mein hona chahiye.

---

## Step 9: Test Karna — API Se Post Karo

### Quick Test via curl:

```bash
curl -X POST "https://api.linkedin.com/v2/ugcPosts" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "author": "urn:li:person:YOUR_PERSON_ID",
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": "Hello from LinkedIn API! 🚀 This is a test post."
            },
            "shareMediaCategory": "NONE"
        }
    },
    "visibility": {
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
}'
```

### Test via FTE Dashboard:

1. Dashboard start karo: `uv run streamlit run src/dashboard/app.py`
2. **Social Media** tab pe jao
3. LinkedIn checkbox enabled hoga (green ✅ Connected)
4. Content likho aur **Post** click karo

### Test via MCP Tool (Claude Code):

Claude Code mein directly:
```
Use the create_linkedin_post tool to post "Test from MCP! 🤖"
```

---

## Step 10: Token Refresh Karna (Har 60 Din)

LinkedIn access token 60 days mein expire hota hai. Refresh karne ke liye:

1. `https://www.linkedin.com/developers/tools/oauth` pe jao
2. Apni app select karo
3. Same scopes select karo
4. **"Request access token"** click karo
5. Naya token `.env` mein update karo

### Token Expiry Check:

```bash
curl -s "https://api.linkedin.com/v2/userinfo" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Agar `401 Unauthorized` aaye toh token expire ho gaya hai.

---

## Troubleshooting

### Error: 403 ACCESS_DENIED (Organization URN)

**Problem:** Organization URN se post karne pe 403 error
**Solution:** Person URN use karo instead of Organization URN

```python
# Wrong ❌
author = "urn:li:organization:112495928"

# Correct ✅
author = "urn:li:person:abc123def456"
```

### Error: Token Expired

**Problem:** `401 Unauthorized` ya `invalid_token`
**Solution:** Step 10 follow karo — naya token generate karo

### Error: Scope Not Available

**Problem:** `w_member_social` scope nahi dikh raha
**Solution:** Developer portal → Products → "Share on LinkedIn" request karo. Approval ke baad scope available hoga.

### Error: Post Not Showing

**Problem:** API success response aaya but post nahi dikh raha
**Solution:**
1. Check karo `visibility` PUBLIC hai
2. Check karo `lifecycleState` PUBLISHED hai
3. LinkedIn app sometimes 2-3 minutes late dikhata hai

---

## Architecture — How It Works in FTE System

```
┌─────────────────────────────────────────────────┐
│              FTE AI Employee System              │
├─────────────────────────────────────────────────┤
│                                                   │
│  Dashboard (Streamlit)                           │
│  └── Social Media Hub                            │
│      └── LinkedIn Section                        │
│          ├── Status Check (userinfo API)         │
│          ├── Compose Post (text input)           │
│          └── Send Post (ugcPosts API)            │
│                                                   │
│  MCP Server (linkedin_server.py)                 │
│  └── Tools:                                      │
│      ├── create_linkedin_post(content)           │
│      ├── get_linkedin_posts()                    │
│      ├── get_linkedin_profile()                  │
│      ├── comment_on_linkedin_post(id, comment)   │
│      └── like_linkedin_post(id)                  │
│                                                   │
│  API Flow:                                       │
│  User/AI → MCP Tool → LinkedIn API → LinkedIn    │
│                                                   │
└─────────────────────────────────────────────────┘
```

### Key Files:

| File | Purpose |
|---|---|
| `src/mcp/linkedin_server.py` | MCP server — LinkedIn API integration |
| `src/dashboard/app.py` | Dashboard — LinkedIn UI section |
| `.env` | API credentials (never commit!) |
| `.claude/skills/linkedin_poster.md` | Claude skill for LinkedIn posting |

---

## Quick Reference Card

| Item | Value |
|---|---|
| **API Base URL** | `https://api.linkedin.com/v2/` |
| **Post Endpoint** | `POST /v2/ugcPosts` |
| **Profile Endpoint** | `GET /v2/userinfo` |
| **Auth Header** | `Authorization: Bearer ACCESS_TOKEN` |
| **Token Lifetime** | 60 days |
| **Required Scope** | `w_member_social` |
| **Author Format** | `urn:li:person:YOUR_ID` |
| **Visibility** | `com.linkedin.ugc.MemberNetworkVisibility: PUBLIC` |

---

## Checklist — Setup Complete?

- [ ] LinkedIn Page created
- [ ] Developer App created
- [ ] "Share on LinkedIn" product enabled
- [ ] "Sign In with LinkedIn" product enabled
- [ ] `w_member_social` scope available
- [ ] Client ID noted
- [ ] Client Secret noted
- [ ] Access Token generated
- [ ] Person URN found
- [ ] Organization URN found (optional)
- [ ] `.env` file updated with all credentials
- [ ] Test post successful via Dashboard
- [ ] Test post successful via MCP tool
- [ ] Calendar reminder set for token refresh (60 days)

---

*Guide created for Agentive Solutions — AI Employee as a Service*
*Last updated: 2026-03-18*
