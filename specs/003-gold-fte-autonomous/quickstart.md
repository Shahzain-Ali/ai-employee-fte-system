# Quickstart: Gold Tier — Autonomous Employee

**Feature**: 003-gold-fte-autonomous
**Prerequisites**: Silver tier fully implemented and working

---

## Overview

Gold tier extends Silver with:
- Odoo Community Edition (Docker) — accounting, invoices, expenses
- Facebook Business Page posting (Meta Graph API via custom MCP)
- Instagram Business/Creator Account publishing (Meta Graph API via custom MCP)
- Cross-domain integration (Personal + Business domains connected)
- Weekly CEO Briefing generation
- Comprehensive audit logging with workflow tracking
- Error recovery with graceful degradation
- Ralph Wiggum autonomous loop (Stop hook)
- All AI functionality as Agent Skills

---

## Step 1: Install Gold Dependencies

```bash
cd /mnt/e/hackathon-0/full-time-equivalent-project

# Add requests for HTTP calls (JSON-RPC + Graph API)
uv add requests
```

Note: `requests` is the only new Python package. Odoo runs in Docker (no Python dep).

---

## Step 2: Docker + Odoo Setup

### 2.1 Verify Docker

```bash
docker --version
docker-compose --version
```

### 2.2 Start Odoo

```bash
# Start Odoo + PostgreSQL
docker-compose -f config/docker-compose.yml up -d

# Wait for Odoo to be ready (~30 seconds)
# Access Odoo at http://localhost:8069
```

### 2.3 Configure Odoo (First Time — Manual)

1. Open http://localhost:8069 in browser
2. Create database (name: `fte_gold`, email: your email, password: choose one)
3. Install "Invoicing" module
4. Install "Expenses" module
5. Set up company details (name, address, currency)

### 2.4 Update .env

```bash
echo 'ODOO_URL=http://localhost:8069' >> .env
echo 'ODOO_DB=fte_gold' >> .env
echo 'ODOO_USER=admin' >> .env
echo 'ODOO_PASSWORD=your_password_here' >> .env
```

---

## Step 3: Meta Developer Account Setup

### 3.1 Create Facebook Business Page

1. Go to facebook.com → Create → Page
2. Page name: your business name
3. Category: your business type
4. Note the **Page ID** (from Page Settings → About)

### 3.2 Convert Instagram to Business or Creator Account

1. Open Instagram app → Settings → Account
2. "Switch to Professional Account" → Choose **Business** or **Creator** (both work with Instagram Platform API since July 2024)
3. Connect to your Facebook Business Page (required for API access, even for Creator accounts)
4. Note the **Instagram Account ID**

### 3.3 Create Meta Developer Account

1. Go to https://developers.facebook.com
2. "Get Started" → Create Developer Account (free)
3. Create New App → Business Type
4. App name: `AI Employee Gold`

### 3.4 Configure App Permissions

1. In App Dashboard → Add Products → Facebook Login
2. Go to App Review → Request permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
   - `instagram_basic`
   - `instagram_content_publish`
3. For development: Use App Roles to add test users

### 3.5 Get Non-Expiring Page Access Token

```bash
# Step 1: Get short-lived user token from Graph API Explorer
# https://developers.facebook.com/tools/explorer/
# Select your app → Get User Access Token → check required permissions

# Step 2: Exchange for long-lived user token
curl "https://graph.facebook.com/v21.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"

# Step 3: Get non-expiring Page token
curl "https://graph.facebook.com/v21.0/me/accounts?\
access_token=YOUR_LONG_LIVED_USER_TOKEN"

# The access_token in the response is your non-expiring Page token
```

### 3.6 Update .env with Meta credentials

```bash
echo 'FB_PAGE_ID=your_page_id' >> .env
echo 'FB_PAGE_ACCESS_TOKEN=your_non_expiring_page_token' >> .env
echo 'IG_USER_ID=your_ig_business_account_id' >> .env
echo 'IG_ACCESS_TOKEN=your_page_access_token' >> .env
echo 'META_API_VERSION=v21.0' >> .env
```

---

## Step 4: Register MCP Servers

Update `.mcp.json` to include all Gold tier servers:

```json
{
  "mcpServers": {
    "fte-email": {
      "type": "stdio",
      "command": "node",
      "args": ["/mnt/e/hackathon-0/full-time-equivalent-project/src/mcp/index.js"],
      "env": {}
    },
    "fte-odoo": {
      "type": "stdio",
      "command": "python",
      "args": ["src/mcp/odoo_server.py"],
      "env": {}
    },
    "fte-facebook": {
      "type": "stdio",
      "command": "python",
      "args": ["src/mcp/facebook_server.py"],
      "env": {}
    },
    "fte-instagram": {
      "type": "stdio",
      "command": "python",
      "args": ["src/mcp/instagram_server.py"],
      "env": {}
    }
  }
}
```

---

## Step 5: Create Gold Vault Directories

```bash
mkdir -p AI_Employee_Vault/Briefings
mkdir -p AI_Employee_Vault/Tasks
```

---

## Step 6: Configure Ralph Wiggum Stop Hook

Create/update `.claude/settings.json`:

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

Make the hook script executable:

```bash
chmod +x scripts/ralph-wiggum-check.sh
```

---

## Step 7: Test Individual Components

### 7.1 Test Odoo MCP

```bash
# Ensure Odoo Docker is running
docker-compose -f config/docker-compose.yml ps

# Test the MCP server manually
python src/mcp/odoo_server.py
# Should output: "Odoo MCP Server running on stdio"
```

### 7.2 Test Facebook MCP

```bash
python src/mcp/facebook_server.py
# Should output: "Facebook MCP Server running on stdio"
```

### 7.3 Test Instagram MCP

```bash
python src/mcp/instagram_server.py
# Should output: "Instagram MCP Server running on stdio"
```

### 7.4 Test CEO Briefing (Manual Trigger)

```bash
python -m src.main briefing
# Should generate CEO_Briefing_YYYY-MM-DD.md in Briefings/
```

---

## Step 8: Start Full Gold System

```bash
# Start Odoo Docker (if not running)
docker-compose -f config/docker-compose.yml up -d

# Start the full system
python -m src.main run
```

---

## Step 9: Verify Dashboard

Open `AI_Employee_Vault/Dashboard.md` in Obsidian.

Should show:
- Financial summary from Odoo
- Social media metrics (Facebook + Instagram)
- System health for all 5 components
- Watcher status table
- Recent cross-domain activity

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Odoo Docker won't start | Check Docker running: `docker ps`. Check ports: `netstat -tlnp \| grep 8069` |
| Odoo MCP connection refused | Verify ODOO_URL in .env. Check Docker: `docker-compose ps` |
| Facebook token expired | Page tokens from long-lived user tokens don't expire. Re-check token generation steps |
| Instagram "not Business/Creator account" | Convert: Instagram Settings → Account → Switch to Professional → Business or Creator |
| Instagram 50-post limit | Wait 24 hours (50 posts/day limit since 2024). Track in audit logs |
| Ralph Wiggum infinite loop | Check max_iterations in task file. Verify scripts/ralph-wiggum-check.sh is executable |
| MCP server not found by Claude | Restart Claude Code after updating .mcp.json |
| CEO Briefing missing data | Check component health in .state/health.json. Ensure all services are running |

---

## Security Checklist

- [ ] ODOO_PASSWORD in .env, not in docker-compose.yml
- [ ] FB_PAGE_ACCESS_TOKEN in .env, not in .mcp.json
- [ ] IG_ACCESS_TOKEN in .env, not in .mcp.json
- [ ] .env in .gitignore
- [ ] .secrets/ in .gitignore
- [ ] .state/ in .gitignore
- [ ] Audit logs don't contain tokens or passwords
- [ ] All MCP servers load credentials from environment variables

---

## Next Steps

1. Run system for 48 hours
2. Review CEO Briefing quality on Monday morning
3. Monitor audit logs for errors
4. Test cross-domain workflow (email → Odoo invoice → email confirmation)
5. Test Ralph Wiggum with a 5-step task
6. Review Dashboard accuracy
