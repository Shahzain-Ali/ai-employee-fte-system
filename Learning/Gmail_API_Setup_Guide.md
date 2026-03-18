# Gmail API — Complete Setup Guide

**Date:** 2026-03-18
**Author:** Shahzain Bangash + Claude Opus 4.6
**Status:** FULLY WORKING — Read, Send, Modify Emails via Gmail API

---

## Overview

Ye guide step-by-step batati hai ke kaise Gmail API setup karke automated email reading, sending, aur management ki ja sakti hai. FTE AI Employee system Gmail API use karta hai emails watch karne, reply karne, aur dashboard se email bhejne ke liye.

### Kya Kya Automate Ho Sakta Hai?

| Action | Supported | How |
|---|---|---|
| Read Emails | YES | Gmail Watcher (auto-polls) |
| Send Emails | YES | Dashboard + MCP Tool |
| Mark as Read | YES | Gmail Watcher (after processing) |
| Search Emails | YES | Gmail API query filters |
| Draft Emails | YES | MCP Email Tool |

### Important Notes
- **Gmail API free hai** — Google Cloud Free Tier mein included
- **OAuth2 required** — App Password nahi chalega, proper OAuth2 flow chahiye
- **Token auto-refresh** — Ek baar setup ke baad token automatically refresh hota rahega
- **Scopes matter** — Sirf wahi permissions milti hain jo scopes mein define hain

---

## Prerequisites (Ye Pehle Se Hona Chahiye)

1. Gmail account (jis se emails send/receive karne hain)
2. Google Cloud Console access (`https://console.cloud.google.com`)

---

## Step 1: Google Cloud Project Create/Select Karna

1. Google Cloud Console kholein: `https://console.cloud.google.com`
2. Top bar mein project dropdown pe click karo
3. **Option A:** Naya project banao → **"New Project"** → Naam do (e.g., "FTE AI Employee") → **Create**
4. **Option B:** Existing project select karo (agar pehle se hai)

> ⚠️ **Free Tier Limit:** Google Cloud mein limited projects ban sakte hain. Agar limit hit ho toh existing project use karo ya purane unused projects delete karo.

---

## Step 2: Gmail API Enable Karna

1. Google Cloud Console mein apna project selected hona chahiye
2. Left sidebar → **APIs & Services** → **Library**
3. Search box mein type karo: **"Gmail API"**
4. **Gmail API** pe click karo
5. **"Enable"** button pe click karo

✅ **Gmail API enabled!**

---

## Step 3: OAuth Consent Screen Configure Karna

> Ye step zaroori hai — bina iske credentials nahi banenge.

1. **APIs & Services** → **OAuth consent screen**
2. User Type select karo:
   - **External** — agar testing ke liye hai (most cases)
   - **Internal** — sirf Google Workspace accounts ke liye
3. **"Create"** click karo

### Consent Screen Details Fill Karo:

| Field | Value | Notes |
|---|---|---|
| **App name** | FTE AI Employee | Ya koi bhi naam |
| **User support email** | apni email | Required |
| **Developer contact email** | apni email | Required |

4. **"Save and Continue"** click karo

### Scopes Add Karo:

1. **"Add or Remove Scopes"** click karo
2. Search karo aur ye scopes select karo:

| Scope | Purpose |
|---|---|
| `https://www.googleapis.com/auth/gmail.readonly` | Emails read karna |
| `https://www.googleapis.com/auth/gmail.modify` | Emails mark as read |
| `https://www.googleapis.com/auth/gmail.send` | Emails send karna |

3. **"Update"** click karo
4. **"Save and Continue"** click karo

### Test Users Add Karo:

1. **"Add Users"** click karo
2. Apni Gmail address add karo (e.g., `alishahzain604@gmail.com`)
3. **"Save and Continue"** click karo

> ⚠️ **Testing Mode:** Jab tak app "In Production" na ho, sirf test users hi use kar sakte hain. Personal use ke liye testing mode kaafi hai.

---

## Step 4: OAuth Client Credentials Create Karna

1. **APIs & Services** → **Credentials**
2. Top pe **"+ Create Credentials"** → **"OAuth client ID"**
3. Application type: **Desktop app**
4. Name: **FTE AI Employee Gmail** (ya koi bhi descriptive naam)
5. **"Create"** click karo

### Credentials Download Karo:

1. Created client pe popup aayega with Client ID aur Client Secret
2. **"Download JSON"** button pe click karo
3. Downloaded file ko rename karo: `gmail_credentials.json`
4. File ko move karo project ke `.secrets/` folder mein:

```
your-project/.secrets/gmail_credentials.json
```

> ⚠️ **NEVER commit this file to git!** `.secrets/` already `.gitignore` mein hona chahiye.

---

## Step 5: Environment Variables Set Karna

`.env` file mein ye variables add karo:

```env
# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=.secrets/gmail_credentials.json
GMAIL_TOKEN_PATH=.secrets/gmail_token.json
```

| Variable | Purpose |
|---|---|
| `GMAIL_CREDENTIALS_PATH` | OAuth client credentials JSON file ka path |
| `GMAIL_TOKEN_PATH` | OAuth token save hoga yahan (auto-generated) |

> ⚠️ **`.env` file ko manually edit karo** — AI agent ko `.env` file read karne ki permission nahi hai.

---

## Step 6: First-Time Authorization (Token Generate Karna)

### Method A: Automatic (Recommended — Jab Browser Available Ho)

Terminal mein run karo:

```bash
uv run python -c "from dotenv import load_dotenv; load_dotenv('.env'); from src.watchers.gmail_auth import get_gmail_credentials; get_gmail_credentials()"
```

**Kya hoga:**
1. Browser automatically open hoga
2. Google account select karo
3. "Allow" pe click karo — sab permissions accept karo
4. Browser mein dikhega: **"The authentication flow has completed. You may close this window."**
5. Token automatically `.secrets/gmail_token.json` mein save ho jayega

✅ **Done! Token saved.**

### Method B: Manual (Jab Browser Auto-Open Na Ho — WSL/Server)

Agar `run_local_server` browser nahi khol pata (WSL, headless server):

**Step B-1:** Server start karo:
```bash
uv run python -c "
from dotenv import load_dotenv; load_dotenv('.env')
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.modify','https://www.googleapis.com/auth/gmail.send']
creds_path = os.getenv('GMAIL_CREDENTIALS_PATH', '.secrets/gmail_credentials.json')
token_path = os.getenv('GMAIL_TOKEN_PATH', '.secrets/gmail_token.json')
flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
print('Open http://localhost:8090 in browser')
creds = flow.run_local_server(port=8090, open_browser=False, prompt='consent')
token_file = Path(token_path)
token_file.parent.mkdir(parents=True, exist_ok=True)
token_file.write_text(creds.to_json(), encoding='utf-8')
print('SUCCESS: Token saved!')
"
```

**Step B-2:** Browser mein open karo: `http://localhost:8090`
**Step B-3:** Google login karo aur permissions allow karo
**Step B-4:** "Authentication flow completed" message aayega — token saved!

### Method C: Manual Code Exchange (Jab State Mismatch Error Aaye)

Agar Method B mein `MismatchingStateError` aaye (browser cache issue):

**Step C-1:** Authorization URL generate karo — `CLIENT_ID` apna daalo:
```
https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID.apps.googleusercontent.com&redirect_uri=http://127.0.0.1:9876&response_type=code&scope=https://www.googleapis.com/auth/gmail.readonly%20https://www.googleapis.com/auth/gmail.modify%20https://www.googleapis.com/auth/gmail.send&access_type=offline&prompt=consent
```

**Step C-2:** Browser mein paste karo (Incognito recommended)
**Step C-3:** Google login karo aur Allow karo
**Step C-4:** Browser "Site can't be reached" dikhayega — **YEH NORMAL HAI!**
**Step C-5:** Address bar se poora URL copy karo — `code=` ke baad wala code nikalo
**Step C-6:** Terminal mein run karo (apna code daalo):

```bash
uv run python -c "
from dotenv import load_dotenv; load_dotenv('.env')
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.modify','https://www.googleapis.com/auth/gmail.send']
creds_path = os.getenv('GMAIL_CREDENTIALS_PATH', '.secrets/gmail_credentials.json')
token_path = os.getenv('GMAIL_TOKEN_PATH', '.secrets/gmail_token.json')
flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES, redirect_uri='http://127.0.0.1:9876')
flow.fetch_token(code='YOUR_CODE_HERE')
token_file = Path(token_path)
token_file.parent.mkdir(parents=True, exist_ok=True)
token_file.write_text(flow.credentials.to_json(), encoding='utf-8')
print('SUCCESS: Token saved!')
print('Valid:', flow.credentials.valid)
"
```

> ⚠️ **Code jaldi paste karo** — authorization codes 5-10 minutes mein expire hote hain!

---

## Step 7: Verify Token Working Hai

```bash
uv run python -c "
from dotenv import load_dotenv; load_dotenv('.env')
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
token_path = os.getenv('GMAIL_TOKEN_PATH', '.secrets/gmail_token.json')
creds = Credentials.from_authorized_user_file(token_path)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
service = build('gmail', 'v1', credentials=creds)
profile = service.users().getProfile(userId='me').execute()
print('Gmail connected:', profile.get('emailAddress'))
print('Total messages:', profile.get('messagesTotal'))
"
```

Expected output:
```
Gmail connected: your@gmail.com
Total messages: 12345
```

✅ **Gmail API fully working!**

---

## Step 8: Test Email Send Karna

### Via Dashboard:

1. Dashboard start karo: `uv run streamlit run src/dashboard/app.py`
2. **Communications** tab pe jao
3. **"Compose New Email"** pe click karo
4. To, Subject, Body fill karo
5. **"Send Email"** click karo

### Via Terminal (Quick Test):

```bash
uv run python -c "
from dotenv import load_dotenv; load_dotenv('.env')
from src.utils.email_sender import send_email
result = send_email('your@gmail.com', 'Test from FTE', 'Hello from AI Employee!')
print('Sent! ID:', result.get('id'))
"
```

### Via MCP Tool (Claude Code):

```
Use the send_email_tool to send an email to your@gmail.com with subject "Test" and body "Hello!"
```

---

## Token Auto-Refresh — Kaise Kaam Karta Hai

```
┌──────────────────────────────────────────────┐
│              Token Lifecycle                  │
├──────────────────────────────────────────────┤
│                                              │
│  First Time:                                 │
│  Browser → Google Login → Allow → Token Save │
│                                              │
│  Normal Use:                                 │
│  Token Load → Valid? → YES → Use API         │
│                        NO  → Refresh Token   │
│                              → New Token     │
│                              → Save & Use    │
│                                              │
│  Token Expired + No Refresh:                 │
│  → Re-authorize (Step 6 again)              │
│                                              │
└──────────────────────────────────────────────┘
```

- **Access Token:** ~1 hour valid, auto-refresh hota hai
- **Refresh Token:** Long-lived, tab tak valid jab tak user revoke na kare
- **Re-authorization:** Sirf tab zaroori jab refresh token bhi expire/revoke ho

---

## Troubleshooting

### Error: Token Expired or Revoked

**Problem:** `invalid_grant: Token has been expired or revoked`
**Cause:** Token expire ho gaya ya Google account se revoke kiya
**Solution:** Step 6 follow karo — naya token generate karo

### Error: MismatchingStateError (CSRF Warning)

**Problem:** `MismatchingStateError: State not equal in request and response`
**Cause:** Browser cache mein purana OAuth request stored hai
**Solution:**
1. Sab localhost tabs band karo
2. Method C use karo (manual code exchange)
3. Ya Incognito window + naya port use karo

### Error: Redirect URI Mismatch

**Problem:** `Error 400: redirect_uri_mismatch`
**Cause:** Google Console mein redirect URI configured nahi
**Solution:** Google Console → Credentials → OAuth Client → Authorized redirect URIs mein add karo:
- `http://localhost:8090/`
- `http://127.0.0.1:9876`

### Error: Access Not Configured

**Problem:** `Gmail API has not been used in project`
**Cause:** Gmail API enable nahi hai
**Solution:** Step 2 follow karo — APIs & Services → Library → Gmail API → Enable

### Error: User Not in Test Users

**Problem:** `Error 403: access_denied` during consent
**Cause:** App testing mode mein hai aur user test users mein nahi hai
**Solution:** OAuth Consent Screen → Test Users → Apni email add karo

### Error: Insufficient Permissions

**Problem:** `Insufficient Permission` when sending email
**Cause:** Token mein `gmail.send` scope nahi hai
**Solution:** Delete `.secrets/gmail_token.json` aur Step 6 se dubara authorize karo with all 3 scopes

---

## Architecture — How It Works in FTE System

```
┌─────────────────────────────────────────────────┐
│              FTE AI Employee System              │
├─────────────────────────────────────────────────┤
│                                                   │
│  Gmail Watcher (src/watchers/gmail_watcher.py)   │
│  └── Polls Gmail every 60 seconds               │
│      ├── New email detected                      │
│      ├── Creates task in Needs_Action/           │
│      └── Marks email as read                     │
│                                                   │
│  Email Sender (src/utils/email_sender.py)        │
│  └── Sends emails via Gmail API                  │
│      ├── Called from Dashboard                   │
│      ├── Called from MCP tool                    │
│      └── Called from approval handler            │
│                                                   │
│  Dashboard (src/dashboard/app.py)                │
│  └── Communications Tab                          │
│      ├── Gmail status (Connected/Not)            │
│      ├── Recent email activity                   │
│      ├── Compose & Send Email form               │
│      └── Communication summary                   │
│                                                   │
│  MCP Server (src/mcp/email_server.py)            │
│  └── Tools:                                      │
│      ├── send_email_tool(to, subject, body)      │
│      └── draft_email_tool(to, subject, body)     │
│                                                   │
│  Gmail Auth (src/watchers/gmail_auth.py)         │
│  └── Token management                            │
│      ├── Load token from .secrets/               │
│      ├── Auto-refresh expired tokens             │
│      └── First-time OAuth flow                   │
│                                                   │
└─────────────────────────────────────────────────┘
```

### Key Files:

| File | Purpose |
|---|---|
| `src/watchers/gmail_auth.py` | OAuth2 token management (load, refresh, authorize) |
| `src/watchers/gmail_watcher.py` | Polls Gmail for new emails |
| `src/utils/email_sender.py` | Sends emails via Gmail API |
| `src/mcp/email_server.py` | MCP server for Claude email tools |
| `src/dashboard/app.py` | Dashboard Communications section |
| `.secrets/gmail_credentials.json` | OAuth client credentials (NEVER commit!) |
| `.secrets/gmail_token.json` | OAuth token (auto-generated, NEVER commit!) |
| `.env` | Environment variables for paths |

---

## Quick Reference Card

| Item | Value |
|---|---|
| **API** | Gmail API v1 |
| **Auth** | OAuth 2.0 (Desktop App flow) |
| **Scopes** | gmail.readonly, gmail.modify, gmail.send |
| **Token Location** | `.secrets/gmail_token.json` |
| **Credentials Location** | `.secrets/gmail_credentials.json` |
| **Token Refresh** | Automatic (via refresh token) |
| **Console URL** | `https://console.cloud.google.com` |
| **API Library** | APIs & Services → Library → Gmail API |

---

## Checklist — Setup Complete?

- [ ] Google Cloud project created/selected
- [ ] Gmail API enabled
- [ ] OAuth Consent Screen configured
- [ ] Test users added (your Gmail)
- [ ] OAuth Client ID created (Desktop app)
- [ ] Credentials JSON downloaded → `.secrets/gmail_credentials.json`
- [ ] `.env` updated with `GMAIL_CREDENTIALS_PATH` and `GMAIL_TOKEN_PATH`
- [ ] First-time authorization completed (token saved)
- [ ] Token verification successful (Gmail connected)
- [ ] Test email sent from Dashboard
- [ ] Test email sent from MCP tool
- [ ] `.secrets/` in `.gitignore`

---

*Guide created for Agentive Solutions — AI Employee as a Service*
*Last updated: 2026-03-18*
