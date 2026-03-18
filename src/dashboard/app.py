"""FTE AI Employee Dashboard — Streamlit application.

Real-time overview of AI employee activities: Finance, Social Media, Communications.
Gold Tier implementation with full MCP server integration.
"""
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
DASHBOARD_FILE = VAULT_PATH / "Dashboard.md"
LOGS_DIR = VAULT_PATH / "Logs"
PLANS_DIR = VAULT_PATH / "Plans"
DONE_DIR = VAULT_PATH / "Done"
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
PENDING_APPROVAL_DIR = VAULT_PATH / "Pending_Approval"
BRIEFINGS_DIR = VAULT_PATH / "Briefings"

# Odoo config
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "fte-ai-employee")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

# Meta API config
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
META_API_VERSION = os.getenv("META_API_VERSION", "v25.0")



# ==================== HELPER FUNCTIONS ====================

def call_meta_api(endpoint: str, token: str, params: Dict = None) -> Dict:
    """Call Meta Graph API."""
    try:
        url = f"https://graph.facebook.com/{META_API_VERSION}/{endpoint}"
        response = requests.get(url, params={**(params or {}), "access_token": token}, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ==================== DATA FETCHERS ====================

def get_odoo_invoices(status: str = "all", limit: int = 10) -> dict:
    """Fetch invoices from Odoo via JSON-RPC."""
    try:
        # Authenticate
        auth_resp = requests.post(f"{ODOO_URL}/jsonrpc", json={
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [ODOO_DB, ODOO_USER, ODOO_PASSWORD, {}]
            },
            "id": 1
        }, timeout=10)
        uid = auth_resp.json().get("result")
        if not uid:
            return {"error": "Authentication failed", "data": []}

        # Get invoices
        domain = [["move_type", "=", "out_invoice"]]
        if status == "draft":
            domain.append(["state", "=", "draft"])
        elif status == "posted":
            domain.append(["state", "=", "posted"])
        elif status == "paid":
            domain.append(["payment_state", "=", "paid"])

        invoices_resp = requests.post(f"{ODOO_URL}/jsonrpc", json={
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    ODOO_DB, uid, ODOO_PASSWORD,
                    "account.move", "search_read",
                    [domain],
                    {
                        "fields": ["id", "name", "partner_id", "amount_total",
                                   "state", "payment_state", "invoice_date", "invoice_date_due"],
                        "limit": limit,
                        "order": "create_date desc"
                    }
                ]
            },
            "id": 2
        }, timeout=10)

        result = invoices_resp.json().get("result", [])
        # Normalize partner_id
        for inv in result:
            if isinstance(inv.get("partner_id"), list):
                inv["partner_id"] = inv["partner_id"][1] if len(inv["partner_id"]) > 1 else "Unknown"
        return {"data": result}
    except Exception as e:
        return {"error": str(e), "data": []}


def get_odoo_weekly_summary() -> dict:
    """Get weekly financial summary from Odoo."""
    try:
        auth_resp = requests.post(f"{ODOO_URL}/jsonrpc", json={
            "jsonrpc": "2.0", "method": "call",
            "params": {"service": "common", "method": "authenticate",
                       "args": [ODOO_DB, ODOO_USER, ODOO_PASSWORD, {}]},
            "id": 1
        }, timeout=10)
        uid = auth_resp.json().get("result")
        if not uid:
            return {"error": "Auth failed", "data": {}}

        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)

        # Paid invoices (revenue)
        paid_resp = requests.post(f"{ODOO_URL}/jsonrpc", json={
            "jsonrpc": "2.0", "method": "call",
            "params": {"service": "object", "method": "execute_kw",
                       "args": [ODOO_DB, uid, ODOO_PASSWORD, "account.move", "search_read",
                                [[["move_type", "=", "out_invoice"],
                                  ["payment_state", "=", "paid"],
                                  ["invoice_date", ">=", str(start)],
                                  ["invoice_date", "<=", str(end)]]],
                                {"fields": ["amount_total"]}]},
            "id": 2
        }, timeout=10)
        total_revenue = sum(inv.get("amount_total", 0) for inv in paid_resp.json().get("result", []))

        # Pending invoices
        pending_resp = requests.post(f"{ODOO_URL}/jsonrpc", json={
            "jsonrpc": "2.0", "method": "call",
            "params": {"service": "object", "method": "execute_kw",
                       "args": [ODOO_DB, uid, ODOO_PASSWORD, "account.move", "search_read",
                                [[["move_type", "=", "out_invoice"],
                                  ["payment_state", "!=", "paid"],
                                  ["state", "=", "posted"]]],
                                {"fields": ["amount_total"]}]},
            "id": 3
        }, timeout=10)
        pending_data = pending_resp.json().get("result", [])
        outstanding = sum(inv.get("amount_total", 0) for inv in pending_data)

        return {
            "data": {
                "week_start": str(start),
                "week_end": str(end),
                "total_revenue": total_revenue,
                "outstanding_balance": outstanding,
                "pending_invoices_count": len(pending_data)
            }
        }
    except Exception as e:
        return {"error": str(e), "data": {}}


def get_facebook_stats() -> Dict:
    """Get Facebook Page statistics via Meta Graph API."""
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        return {"error": "Facebook not configured", "data": {}}

    try:
        # Get page info
        page_data = call_meta_api(FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN,
                                   {"fields": "name,followers_count,fan_count"})

        # Get recent posts
        posts_data = call_meta_api(f"{FB_PAGE_ID}/posts", FB_PAGE_ACCESS_TOKEN,
                                    {"fields": "message,created_time,likes.summary(true),comments.summary(true)", "limit": 5})

        # Get insights (last 7 days)
        insights_data = call_meta_api(f"{FB_PAGE_ID}/insights", FB_PAGE_ACCESS_TOKEN,
                                       {"metric": "page_impressions,page_engaged_users", "period": "week"})

        return {
            "data": {
                "page_name": page_data.get("name", "Unknown"),
                "followers": page_data.get("followers_count", 0) or page_data.get("fan_count", 0),
                "recent_posts": posts_data.get("data", []),
                "insights": insights_data.get("data", [])
            }
        }
    except Exception as e:
        return {"error": str(e), "data": {}}


def get_instagram_stats() -> Dict:
    """Get Instagram statistics via Meta Graph API."""
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        return {"error": "Instagram not configured", "data": {}}

    try:
        # Get account info
        account_data = call_meta_api(IG_USER_ID, IG_ACCESS_TOKEN,
                                      {"fields": "username,name,followers_count,media_count"})

        # Get recent media
        media_data = call_meta_api(f"{IG_USER_ID}/media", IG_ACCESS_TOKEN,
                                    {"fields": "caption,media_type,timestamp,like_count,comments_count", "limit": 5})

        # Get insights
        insights_data = call_meta_api(f"{IG_USER_ID}/insights", IG_ACCESS_TOKEN,
                                       {"metric": "impressions,reach,profile_views", "period": "week"})

        return {
            "data": {
                "username": account_data.get("username", "Unknown"),
                "followers": account_data.get("followers_count", 0),
                "media_count": account_data.get("media_count", 0),
                "recent_media": media_data.get("data", []),
                "insights": insights_data.get("data", [])
            }
        }
    except Exception as e:
        return {"error": str(e), "data": {}}


def get_vault_stats() -> dict:
    """Get stats from vault files."""
    stats = {
        "needs_action": 0,
        "pending_approval": 0,
        "plans": 0,
        "done": 0,
        "logs_today": 0,
    }

    if NEEDS_ACTION_DIR.exists():
        stats["needs_action"] = len(list(NEEDS_ACTION_DIR.glob("*.md")))
    if PENDING_APPROVAL_DIR.exists():
        stats["pending_approval"] = len(list(PENDING_APPROVAL_DIR.glob("APPROVAL_*.md")))
    if PLANS_DIR.exists():
        stats["plans"] = len(list(PLANS_DIR.glob("PLAN_*.md")))
    if DONE_DIR.exists():
        stats["done"] = len(list(DONE_DIR.glob("*.md")))
    if LOGS_DIR.exists():
        today = datetime.now().strftime("%Y-%m-%d")
        stats["logs_today"] = len([f for f in LOGS_DIR.glob("*.json") if today in f.name])

    return stats


def get_mcp_server_status() -> dict:
    """Check which MCP servers are configured in .mcp.json."""
    mcp_config_path = PROJECT_ROOT / ".mcp.json"
    servers = {
        "fte-email": False,
        "fte-odoo": False,
        "fte-facebook": False,
        "fte-instagram": False,
        "fte-twitter": False,
        "fte-linkedin": False,
    }
    if mcp_config_path.exists():
        try:
            data = json.loads(mcp_config_path.read_text(encoding="utf-8"))
            configured = data.get("mcpServers", {})
            for name in servers:
                servers[name] = name in configured
        except Exception:
            pass
    return servers


def get_recent_activity(limit: int = 10) -> list:
    """Get recent activity from Done/ folder."""
    activities = []
    if not DONE_DIR.exists():
        return activities

    for f in sorted(DONE_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
        try:
            content = f.read_text()
            # Extract key info from frontmatter
            lines = content.split("\n")
            activity = {"file": f.name}
            for line in lines:
                if line.startswith("skill:"):
                    activity["skill"] = line.split(":", 1)[1].strip()
                elif line.startswith("status:"):
                    activity["status"] = line.split(":", 1)[1].strip()
                elif line.startswith("completed_at:"):
                    activity["time"] = line.split(":", 1)[1].strip()
            activities.append(activity)
        except Exception:
            pass
    return activities


def get_platform_connection_status() -> Dict[str, bool]:
    """Get simplified connection status for all platforms (Connected/Not Connected only)."""
    status = {
        "email": False,
        "whatsapp": False,
        "odoo": False,
        "facebook": False,
        "instagram": False,
        "twitter": False,
        "linkedin": False
    }

    # Email - check credentials
    creds_path = PROJECT_ROOT / ".secrets" / "gmail_credentials.json"
    token_path = PROJECT_ROOT / ".secrets" / "gmail_token.json"
    status["email"] = creds_path.exists() and token_path.exists()

    # WhatsApp - check session
    whatsapp_session = os.getenv("WHATSAPP_SESSION_PATH", ".sessions/whatsapp")
    status["whatsapp"] = Path(whatsapp_session).exists()

    # Odoo - check if accessible
    try:
        resp = requests.get(f"{ODOO_URL}/web/database/selector", timeout=2)
        status["odoo"] = resp.status_code == 200
    except Exception:
        status["odoo"] = False

    # Facebook - check credentials AND test API
    if FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN:
        try:
            fb_stats = get_facebook_stats()
            status["facebook"] = "error" not in fb_stats
        except Exception:
            status["facebook"] = False

    # Instagram - check credentials AND test API
    if IG_USER_ID and IG_ACCESS_TOKEN:
        try:
            ig_stats = get_instagram_stats()
            status["instagram"] = "error" not in ig_stats
        except Exception:
            status["instagram"] = False

    # Twitter - check credentials
    twitter_api_key = os.getenv("TWITTER_API_KEY", "")
    twitter_api_secret = os.getenv("TWITTER_API_SECRET", "")
    status["twitter"] = bool(twitter_api_key and twitter_api_secret)

    # LinkedIn - check API credentials
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    linkedin_person = os.getenv("LINKEDIN_PERSON_URN", "")
    status["linkedin"] = bool(linkedin_token and linkedin_person)

    return status


def get_latest_ceo_briefing() -> Dict:
    """Get the latest CEO Briefing content."""
    if not BRIEFINGS_DIR.exists():
        return {"error": "No briefings directory", "content": ""}

    briefings = sorted(BRIEFINGS_DIR.glob("CEO_Briefing_*.md"), reverse=True)
    if not briefings:
        return {"error": "No briefings found", "content": ""}

    try:
        content = briefings[0].read_text(encoding="utf-8")
        return {"content": content, "file": briefings[0].name}
    except Exception as e:
        return {"error": str(e), "content": ""}


def get_pending_approvals_list() -> List[Dict]:
    """Get list of pending approvals with details."""
    if not PENDING_APPROVAL_DIR.exists():
        return []

    approvals = []
    for f in sorted(PENDING_APPROVAL_DIR.glob("APPROVAL_*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            content = f.read_text(encoding="utf-8")
            # Extract key info from frontmatter
            approval = {
                "file": f.name,
                "created": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "type": "Unknown",
                "summary": ""
            }

            lines = content.split("\n")
            for line in lines:
                if line.startswith("action_type:"):
                    approval["type"] = line.split(":", 1)[1].strip()
                elif line.startswith("## Summary"):
                    # Get next non-empty line
                    idx = lines.index(line)
                    for i in range(idx + 1, min(idx + 5, len(lines))):
                        if lines[i].strip():
                            approval["summary"] = lines[i].strip()[:100]
                            break

            approvals.append(approval)
        except Exception:
            pass

    return approvals


def get_dashboard_content() -> str:
    """Read current Dashboard.md content."""
    if DASHBOARD_FILE.exists():
        return DASHBOARD_FILE.read_text()
    return ""


# ==================== UI COMPONENTS ====================

def render_header():
    """Render dashboard header and setup page config."""
    st.set_page_config(
        page_title="FTE AI Employee Dashboard",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
    <style>
    /* Main header */
    .main-header {
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 15px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 1.8rem;
    }
    .main-header p {
        color: #a0c4e8;
        margin: 5px 0 0 0;
        font-size: 0.9rem;
    }

    /* Status indicators */
    .status-connected { color: #28a745; font-weight: bold; }
    .status-disconnected { color: #dc3545; font-weight: bold; }

    /* Metric cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #2d5a87;
    }
    .metric-label {
        color: #666;
        font-size: 0.9rem;
        margin-top: 5px;
    }

    /* Approval card */
    .approval-card {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1e1e2e;
    }

    /* Sidebar button styling — fix hover visibility */
    [data-testid="stSidebar"] button {
        background-color: #2d2d44 !important;
        color: #ffffff !important;
        border: 1px solid #3d3d5c !important;
        border-radius: 8px !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stSidebar"] button:hover {
        background-color: #4a4a7a !important;
        color: #ffffff !important;
        border-color: #6a6aaa !important;
    }
    [data-testid="stSidebar"] button:focus {
        background-color: #5a5a9a !important;
        color: #ffffff !important;
    }

    /* Sidebar text color */
    [data-testid="stSidebar"] .stMarkdown {
        color: #e0e0e0 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header"><h1>🤖 FTE AI Employee Dashboard</h1><p>Gold Tier — Autonomous Employee</p></div>', unsafe_allow_html=True)


def render_overview():
    """Render Overview section with comprehensive stats."""
    st.header("📊 Overview")

    stats = get_vault_stats()

    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📥 Needs Action", stats["needs_action"])
    with col2:
        st.metric("⏳ Pending Approval", stats["pending_approval"],
                  delta="Requires attention" if stats["pending_approval"] > 0 else None)
    with col3:
        st.metric("📋 Active Plans", stats["plans"])
    with col4:
        st.metric("✅ Completed", stats["done"])
    with col5:
        st.metric("📝 Today's Logs", stats["logs_today"])

    st.divider()

    # System Status with simplified indicators
    st.subheader("🔌 System Status")

    platform_status = get_platform_connection_status()

    # Display in a clean grid
    col1, col2, col3, col4 = st.columns(4)

    platforms = [
        ("Email", "email", col1),
        ("WhatsApp", "whatsapp", col1),
        ("Odoo", "odoo", col2),
        ("Facebook", "facebook", col2),
        ("Instagram", "instagram", col3),
        ("Twitter", "twitter", col3),
        ("LinkedIn", "linkedin", col4),
    ]

    for name, key, col in platforms:
        with col:
            is_connected = platform_status.get(key, False)
            icon = "🟢" if is_connected else "🔴"
            status_text = "Connected" if is_connected else "Not Connected"
            st.markdown(f"{icon} **{name}**: {status_text}")

    st.divider()

    # Recent Activity
    st.subheader("📋 Recent Activity")
    activities = get_recent_activity(10)
    if activities:
        for act in activities:
            skill = act.get('skill', 'N/A')
            status = act.get('status', 'N/A')
            time = act.get('time', '')[:16]
            st.markdown(f"- **{skill}** — `{status}` — *{time}*")
    else:
        st.info("No recent activity recorded")

    # Pending Approvals Alert
    if stats["pending_approval"] > 0:
        st.divider()
        st.warning(f"⚠️ **{stats['pending_approval']} items awaiting your approval**")
        approvals = get_pending_approvals_list()
        for approval in approvals[:3]:
            with st.expander(f"📄 {approval['type']} — {approval['created']}"):
                st.write(f"**File**: `{approval['file']}`")
                st.write(f"**Summary**: {approval['summary']}")
                st.write(f"**Action**: Move to `Approved/` or `Rejected/` folder")

        if len(approvals) > 3:
            st.info(f"+ {len(approvals) - 3} more approvals pending")


def check_odoo_setup() -> bool:
    """Check if Odoo docker setup exists."""
    # Check both possible locations for docker-compose
    config_compose = PROJECT_ROOT / "config" / "docker-compose-odoo.yml"
    legacy_compose = PROJECT_ROOT / "docker" / "odoo" / "docker-compose.yml"
    has_compose = config_compose.exists() or legacy_compose.exists()
    # Also check if ODOO_PASSWORD is configured (not empty default)
    has_password = bool(os.getenv("ODOO_PASSWORD", ""))
    return has_compose or has_password


def check_odoo_running() -> bool:
    """Check if Odoo containers are running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        containers = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return any("odoo" in c.lower() for c in containers)
    except Exception:
        return False


def start_odoo_containers() -> tuple[bool, str]:
    """Start Odoo Docker containers.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        odoo_dir = PROJECT_ROOT / "docker" / "odoo"
        if not odoo_dir.exists():
            return False, "Odoo docker directory not found"

        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=str(odoo_dir),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return True, "Odoo containers started successfully"
        else:
            return False, f"Failed to start: {result.stderr}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def render_finance():
    """Render Finance section (Odoo) with smart container management."""
    st.header("💰 Finance — Odoo Accounting")

    # Check if Odoo is set up
    odoo_setup = check_odoo_setup()

    if not odoo_setup:
        st.error("🔴 Odoo Not Set Up")
        st.warning("⚠️ Odoo accounting system needs to be installed first.")

        st.markdown("""
        ### 📦 Odoo Setup Required

        Odoo is a free, open-source accounting system that runs in Docker containers.

        **Quick Setup (5 minutes):**

        1. **Create Odoo directory:**
        ```bash
        mkdir -p docker/odoo
        cd docker/odoo
        ```

        2. **Create docker-compose.yml:**
        ```yaml
        version: '3.1'
        services:
          postgres:
            image: postgres:15
            environment:
              - POSTGRES_DB=postgres
              - POSTGRES_PASSWORD=odoo
              - POSTGRES_USER=odoo
            volumes:
              - odoo-db-data:/var/lib/postgresql/data

          odoo:
            image: odoo:17
            depends_on:
              - postgres
            ports:
              - "8069:8069"
            environment:
              - HOST=postgres
              - USER=odoo
              - PASSWORD=odoo
            volumes:
              - odoo-web-data:/var/lib/odoo

        volumes:
          odoo-web-data:
          odoo-db-data:
        ```

        3. **Start Odoo:**
        ```bash
        docker-compose up -d
        ```

        4. **Access Odoo:**
        - Open: http://localhost:8069
        - Create database: `fte-ai-employee`
        - Set master password: `admin`
        - Login: admin / admin

        5. **Configure .env:**
        ```env
        ODOO_URL=http://localhost:8069
        ODOO_DB=fte-ai-employee
        ODOO_USER=admin
        ODOO_PASSWORD=admin
        ```

        6. **Refresh this dashboard**

        ---

        **Need help?** Check `Learning/` directory for detailed Odoo setup guides.
        """)

        return

    # Odoo is set up - check if running
    odoo_running = check_odoo_running()

    # Connection status with smart management
    col1, col2 = st.columns([3, 1])

    with col1:
        if odoo_running:
            st.markdown('<p class="status-connected">🟢 Odoo Connected</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-disconnected">🔴 Odoo Disconnected</p>', unsafe_allow_html=True)

    with col2:
        if odoo_running:
            if st.button("🔄 Sync Data"):
                st.rerun()
        else:
            if st.button("▶️ Start Odoo", type="primary"):
                with st.spinner("Starting Odoo containers... This may take 30-40 seconds..."):
                    success, message = start_odoo_containers()

                    if success:
                        st.success(f"✅ {message}")
                        # Wait a bit for Odoo to fully start
                        import time
                        time.sleep(5)
                        st.info("⏳ Odoo is starting up. Please wait 20-30 seconds then refresh.")
                    else:
                        st.error(f"❌ {message}")

    if not odoo_running:
        st.warning("⚠️ Odoo is not running. Click 'Start Odoo' to launch containers.")

        with st.expander("📖 Manual Start Instructions"):
            st.code("""
# Navigate to Odoo directory
cd docker/odoo

# Start containers
docker-compose up -d

# Check status
docker ps | grep odoo

# View logs
docker-compose logs -f odoo
            """, language="bash")
        return

    # Odoo is running - show data
    st.divider()

    # Weekly summary
    st.subheader("📊 Weekly Summary")
    with st.spinner("Loading weekly summary..."):
        summary = get_odoo_weekly_summary()

    if "error" in summary:
        st.error(f"❌ Error: {summary['error']}")
        st.info("💡 Odoo might still be starting up. Wait 30 seconds and refresh.")
    else:
        data = summary.get("data", {})
        col1, col2, col3 = st.columns(3)

        with col1:
            revenue = data.get('total_revenue', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">PKR {revenue:,.0f}</div>
                <div class="metric-label">Weekly Revenue</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            outstanding = data.get('outstanding_balance', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">PKR {outstanding:,.0f}</div>
                <div class="metric-label">Outstanding Balance</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            pending = data.get('pending_invoices_count', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{pending}</div>
                <div class="metric-label">Pending Invoices</div>
            </div>
            """, unsafe_allow_html=True)

        st.caption(f"Week: {data.get('week_start', '')} to {data.get('week_end', '')}")

    st.divider()

    # Invoices section
    st.subheader("📄 Invoices")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        status_filter = st.selectbox("Filter by Status", ["all", "draft", "posted", "paid"])
    with col2:
        limit = st.number_input("Show", min_value=5, max_value=50, value=10, step=5)
    with col3:
        if st.button("➕ Create"):
            st.info("Create invoice via Odoo web interface")

    with st.spinner("Loading invoices..."):
        invoices = get_odoo_invoices(status=status_filter, limit=limit)

    if "error" in invoices:
        st.error(f"❌ Error: {invoices['error']}")
    elif invoices.get("data"):
        import pandas as pd
        df = pd.DataFrame(invoices["data"])

        # Format columns
        display_df = df[["name", "partner_id", "amount_total", "state", "payment_state", "invoice_date_due"]].copy()
        display_df.columns = ["Invoice #", "Partner", "Amount (PKR)", "State", "Payment", "Due Date"]
        display_df["Amount (PKR)"] = display_df["Amount (PKR)"].apply(lambda x: f"{x:,.2f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Invoice status legend
        with st.expander("ℹ️ Invoice Status Guide"):
            st.markdown("""
            **State**:
            - `draft`: Just created, not sent to client
            - `posted`: Confirmed and sent to client
            - `cancel`: Cancelled invoice

            **Payment State**:
            - `not_paid`: No payment received
            - `in_payment`: Payment in progress
            - `paid`: Fully paid
            - `partial`: Partially paid
            """)
    else:
        st.info("No invoices found")

    st.divider()

    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Generate CEO Briefing"):
            st.info("CEO Briefing generation triggered")

    with col2:
        if st.button("📥 Export Report"):
            st.info("Export functionality coming soon")

    with col3:
        if st.button("🌐 Open Odoo Web"):
            st.markdown(f"[Open Odoo]({ODOO_URL})", unsafe_allow_html=True)


def create_social_post(message: str, platforms: List[str]) -> Dict[str, Any]:
    """Create a post on selected social media platforms via MCP servers.

    Args:
        message: Post content
        platforms: List of platform names (e.g., ['facebook', 'instagram'])

    Returns:
        Dict with success status and results per platform
    """
    results = {}

    for platform in platforms:
        try:
            if platform == 'facebook' and FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN:
                # Call Facebook MCP server directly
                url = f"https://graph.facebook.com/{META_API_VERSION}/{FB_PAGE_ID}/feed"
                response = requests.post(url, data={
                    'message': message,
                    'access_token': FB_PAGE_ACCESS_TOKEN
                }, timeout=10)

                if response.status_code == 200:
                    results[platform] = {"success": True, "data": response.json()}
                else:
                    results[platform] = {"success": False, "error": response.text}

            elif platform == 'instagram' and IG_USER_ID and IG_ACCESS_TOKEN:
                # Instagram requires image URL - for text-only, we'll show limitation
                results[platform] = {
                    "success": False,
                    "error": "Instagram requires an image. Text-only posts not supported."
                }

            elif platform == 'linkedin':
                # LinkedIn API posting
                linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
                linkedin_person = os.getenv("LINKEDIN_PERSON_URN", "")
                linkedin_org = os.getenv("LINKEDIN_ORGANIZATION_URN", "")
                author = linkedin_person or linkedin_org

                if linkedin_token and author:
                    url = "https://api.linkedin.com/v2/ugcPosts"
                    headers = {
                        "Authorization": f"Bearer {linkedin_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0",
                        "LinkedIn-Version": "202401"
                    }
                    payload = {
                        "author": author,
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {"text": message},
                                "shareMediaCategory": "NONE"
                            }
                        },
                        "visibility": {
                            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                        }
                    }
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    if response.status_code in [200, 201]:
                        results[platform] = {"success": True, "data": response.json()}
                    else:
                        results[platform] = {"success": False, "error": response.text}
                else:
                    results[platform] = {"success": False, "error": "LinkedIn credentials not configured"}

        except Exception as e:
            results[platform] = {"success": False, "error": str(e)}

    return results


def render_social_media():
    """Render Social Media section with simplified status and post creation."""
    st.header("📱 Social Media Hub")

    platform_status = get_platform_connection_status()

    # Platform status overview
    st.subheader("🔌 Platform Status")
    col1, col2, col3, col4 = st.columns(4)

    platforms_display = [
        ("Facebook", "facebook", col1),
        ("Instagram", "instagram", col2),
        ("Twitter/X", "twitter", col3),
        ("LinkedIn", "linkedin", col4)
    ]

    for name, key, col in platforms_display:
        with col:
            is_connected = platform_status.get(key, False)
            if is_connected:
                st.markdown(f"**{name}**<br/><span class='status-connected'>🟢 Connected</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{name}**<br/><span class='status-disconnected'>🔴 Not Connected</span>", unsafe_allow_html=True)

    st.divider()

    # Post Creation Section
    st.subheader("📝 Create Post")

    # Initialize session state for post creation
    if 'show_post_form' not in st.session_state:
        st.session_state.show_post_form = False
    if 'show_post_preview' not in st.session_state:
        st.session_state.show_post_preview = False

    # Create Post Button
    if not st.session_state.show_post_form and not st.session_state.show_post_preview:
        if st.button("➕ Create New Post", type="primary"):
            st.session_state.show_post_form = True
            st.rerun()

    # Post Creation Form
    if st.session_state.show_post_form:
        with st.form("post_creation_form"):
            st.markdown("### ✍️ Compose Your Post")

            message = st.text_area(
                "Message",
                placeholder="Write your post here...",
                height=150,
                help="This message will be posted to all selected platforms"
            )

            st.markdown("**Select Platforms:**")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                post_to_facebook = st.checkbox(
                    "Facebook",
                    value=platform_status.get('facebook', False),
                    disabled=not platform_status.get('facebook', False)
                )
            with col2:
                post_to_instagram = st.checkbox(
                    "Instagram",
                    value=False,
                    disabled=True,
                    help="Instagram requires image upload (coming soon)"
                )
            with col3:
                post_to_twitter = st.checkbox(
                    "Twitter/X",
                    value=False,
                    disabled=True,
                    help="Twitter integration coming soon"
                )
            with col4:
                post_to_linkedin = st.checkbox(
                    "LinkedIn",
                    value=platform_status.get('linkedin', False),
                    disabled=not platform_status.get('linkedin', False),
                    help="Post to LinkedIn via API"
                )

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("📋 Preview Post", type="primary", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

            if cancel:
                st.session_state.show_post_form = False
                st.rerun()

            if submit:
                if not message.strip():
                    st.error("❌ Please enter a message")
                else:
                    selected_platforms = []
                    if post_to_facebook:
                        selected_platforms.append('facebook')
                    if post_to_instagram:
                        selected_platforms.append('instagram')
                    if post_to_linkedin:
                        selected_platforms.append('linkedin')

                    if not selected_platforms:
                        st.error("❌ Please select at least one platform")
                    else:
                        # Store in session state for preview
                        st.session_state.post_message = message
                        st.session_state.post_platforms = selected_platforms
                        st.session_state.show_post_form = False
                        st.session_state.show_post_preview = True
                        st.rerun()

    # Post Preview & Confirmation
    if st.session_state.show_post_preview:
        st.markdown("### 👀 Review Your Post")

        with st.container():
            st.markdown("**Message:**")
            st.info(st.session_state.post_message)

            st.markdown("**Will post to:**")
            for platform in st.session_state.post_platforms:
                st.markdown(f"✓ {platform.title()}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve & Post", type="primary", use_container_width=True):
                with st.spinner("Posting..."):
                    results = create_social_post(
                        st.session_state.post_message,
                        st.session_state.post_platforms
                    )

                    # Show results
                    success_count = sum(1 for r in results.values() if r.get('success'))

                    if success_count == len(results):
                        st.success(f"✅ Successfully posted to {success_count} platform(s)!")
                    else:
                        st.warning(f"⚠️ Posted to {success_count}/{len(results)} platform(s)")

                    # Show details
                    for platform, result in results.items():
                        if result.get('success'):
                            st.success(f"✅ {platform.title()}: Posted successfully")
                        else:
                            st.error(f"❌ {platform.title()}: {result.get('error', 'Unknown error')}")

                # Reset state
                st.session_state.show_post_preview = False
                st.session_state.post_message = None
                st.session_state.post_platforms = None

        with col2:
            if st.button("🔙 Back to Edit", use_container_width=True):
                st.session_state.show_post_preview = False
                st.session_state.show_post_form = True
                st.rerun()

    st.divider()

    # Facebook Section (if connected)
    if platform_status.get('facebook'):
        st.subheader("📘 Facebook Page")

        with st.spinner("Loading Facebook data..."):
            fb_data = get_facebook_stats()

        if "error" in fb_data:
            st.error(f"❌ Error: {fb_data['error']}")
        else:
            data = fb_data.get("data", {})

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Page**: {data.get('page_name', 'Unknown')}")
                st.metric("👥 Followers", f"{data.get('followers', 0):,}")

            # Recent posts
            posts = data.get("recent_posts", [])
            if posts:
                st.markdown("**Recent Posts**")
                for post in posts[:5]:
                    message = post.get("message", "No caption")[:100]
                    created = post.get("created_time", "")[:10]
                    likes = post.get("likes", {}).get("summary", {}).get("total_count", 0)
                    comments = post.get("comments", {}).get("summary", {}).get("total_count", 0)

                    with st.expander(f"📄 {created} — {message}..."):
                        st.write(f"**Message**: {post.get('message', 'No caption')}")
                        st.write(f"**Engagement**: {likes} likes, {comments} comments")
            else:
                st.info("No recent posts found")

    else:
        st.info("📘 Facebook not connected. Configure FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN in .env")

    st.divider()

    # Instagram Section (if connected)
    if platform_status.get('instagram'):
        st.subheader("📸 Instagram")

        with st.spinner("Loading Instagram data..."):
            ig_data = get_instagram_stats()

        if "error" in ig_data:
            st.error(f"❌ Error: {ig_data['error']}")
        else:
            data = ig_data.get("data", {})

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Account**: @{data.get('username', 'Unknown')}")
            with col2:
                st.metric("👥 Followers", f"{data.get('followers', 0):,}")
            with col3:
                st.metric("📸 Posts", f"{data.get('media_count', 0):,}")

            # Recent media
            media = data.get("recent_media", [])
            if media:
                st.markdown("**Recent Posts**")
                for item in media[:5]:
                    caption = item.get("caption", "No caption")[:100]
                    media_type = item.get("media_type", "UNKNOWN")
                    timestamp = item.get("timestamp", "")[:10]
                    likes = item.get("like_count", 0)
                    comments = item.get("comments_count", 0)

                    with st.expander(f"📷 {timestamp} — {media_type} — {caption}..."):
                        st.write(f"**Caption**: {item.get('caption', 'No caption')}")
                        st.write(f"**Type**: {media_type}")
                        st.write(f"**Engagement**: {likes} likes, {comments} comments")
            else:
                st.info("No recent media found")

    else:
        st.info("📸 Instagram not connected. Configure IG_USER_ID and IG_ACCESS_TOKEN in .env")

    st.divider()

    # Twitter section
    st.subheader("🐦 Twitter/X")
    if platform_status.get('twitter'):
        st.markdown('<span class="status-connected">🟢 Connected</span>', unsafe_allow_html=True)
    else:
        st.info("🔴 Not Connected — Configure TWITTER_API_KEY in .env")

    st.divider()

    # LinkedIn section
    st.subheader("💼 LinkedIn")
    if platform_status.get('linkedin'):
        st.markdown('<span class="status-connected">🟢 Connected</span>', unsafe_allow_html=True)
        # Show LinkedIn profile info
        linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        if linkedin_token:
            try:
                resp = requests.get(
                    "https://api.linkedin.com/v2/userinfo",
                    headers={"Authorization": f"Bearer {linkedin_token}"},
                    timeout=10
                )
                if resp.status_code == 200:
                    profile = resp.json()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Profile**: {profile.get('name', 'Unknown')}")
                    with col2:
                        st.markdown(f"**Email**: {profile.get('email', 'N/A')}")
            except Exception:
                st.write("Profile info unavailable")
    else:
        st.info("🔴 Not Connected — Configure LINKEDIN_ACCESS_TOKEN in .env")


def render_communications():
    """Render Communications section (Email + WhatsApp) with real status."""
    st.header("💬 Communications")

    col1, col2 = st.columns(2)

    # Gmail Section
    with col1:
        st.subheader("📧 Gmail")

        gmail_connected = False
        creds_path = PROJECT_ROOT / ".secrets" / "gmail_credentials.json"
        token_path = PROJECT_ROOT / ".secrets" / "gmail_token.json"

        if creds_path.exists() and token_path.exists():
            gmail_connected = True

        if gmail_connected:
            st.markdown('<p class="status-connected">● Connected</p>', unsafe_allow_html=True)

            # Get email stats from vault
            email_files = list(DONE_DIR.glob("EMAIL_*.md")) if DONE_DIR.exists() else []
            today = datetime.now().date()
            today_emails = [f for f in email_files
                           if datetime.fromtimestamp(f.stat().st_mtime).date() == today]

            st.metric("📨 Emails Processed Today", len(today_emails))
            st.metric("📬 Total Processed", len(email_files))

            # Recent email activity
            if email_files:
                st.markdown("**Recent Email Activity**")
                for f in sorted(email_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    timestamp = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    st.write(f"- `{timestamp}` — {f.name}")
            else:
                st.info("No email activity yet")

            if st.button("🔄 Refresh Gmail", key="refresh_gmail"):
                st.info("Gmail watcher will check on next poll cycle")

        else:
            st.markdown('<p class="status-disconnected">● Not Connected</p>', unsafe_allow_html=True)
            st.warning("Gmail OAuth2 credentials not found")

            with st.expander("📖 Setup Instructions"):
                st.markdown("""
                1. Create OAuth2 credentials in Google Cloud Console
                2. Save as `.secrets/gmail_credentials.json`
                3. Run authorization:
                ```bash
                uv run python -m src.main gmail --authorize
                ```
                4. Token will be saved to `.secrets/gmail_token.json`
                """)

    # WhatsApp Section
    with col2:
        st.subheader("💬 WhatsApp")

        # Check WhatsApp configuration
        whatsapp_configured = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"

        if whatsapp_configured:
            st.markdown('<p class="status-connected">● Configured</p>', unsafe_allow_html=True)

            # Get WhatsApp stats from vault
            wa_files = list(DONE_DIR.glob("WA_*.md")) if DONE_DIR.exists() else []
            today = datetime.now().date()
            today_wa = [f for f in wa_files
                       if datetime.fromtimestamp(f.stat().st_mtime).date() == today]

            st.metric("💬 Messages Processed Today", len(today_wa))
            st.metric("📱 Total Processed", len(wa_files))

            # Recent WhatsApp activity
            if wa_files:
                st.markdown("**Recent WhatsApp Activity**")
                for f in sorted(wa_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    timestamp = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    st.write(f"- `{timestamp}` — {f.name}")
            else:
                st.info("No WhatsApp activity yet")

        else:
            st.markdown('<p class="status-disconnected">● Not Configured</p>', unsafe_allow_html=True)
            st.info("WhatsApp automation via Playwright")

            with st.expander("📖 Setup Instructions"):
                st.markdown("""
                1. Add to `.env`:
                ```
                WHATSAPP_ENABLED=true
                WHATSAPP_PHONE=+92XXXXXXXXXX
                ```
                2. Start orchestrator — Playwright will open WhatsApp Web
                3. Scan QR code to authenticate
                4. Session will be saved for future use
                """)

    st.divider()

    # Compose & Send Email
    st.subheader("✉️ Compose & Send Email")

    if 'show_email_form' not in st.session_state:
        st.session_state.show_email_form = False
    if 'email_sent' not in st.session_state:
        st.session_state.email_sent = False

    if not st.session_state.show_email_form and not st.session_state.email_sent:
        if st.button("📝 Compose New Email", type="primary", key="compose_email"):
            st.session_state.show_email_form = True
            st.rerun()

    if st.session_state.show_email_form:
        with st.form("email_compose_form"):
            st.markdown("### ✍️ New Email")
            email_to = st.text_input("To", placeholder="recipient@example.com")
            email_subject = st.text_input("Subject", placeholder="Email subject...")
            email_body = st.text_area("Body", placeholder="Write your email here...", height=200)

            col1, col2 = st.columns(2)
            with col1:
                send_btn = st.form_submit_button("📤 Send Email", type="primary", use_container_width=True)
            with col2:
                cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)

            if cancel_btn:
                st.session_state.show_email_form = False
                st.rerun()

            if send_btn:
                if not email_to or not email_subject or not email_body:
                    st.error("❌ Please fill all fields")
                else:
                    # Send via Gmail API
                    try:
                        from google.oauth2.credentials import Credentials

                        # Pre-check: verify token exists and is valid before calling send
                        token_path = os.getenv("GMAIL_TOKEN_PATH", ".secrets/gmail_token.json")
                        token_file = Path(token_path)
                        if not token_file.exists():
                            st.error("❌ Gmail token not found. Run the Gmail watcher first to authorize.")
                        else:
                            creds = Credentials.from_authorized_user_file(str(token_file))
                            if creds and creds.expired and creds.refresh_token:
                                from google.auth.transport.requests import Request
                                creds.refresh(Request())
                            if not creds or not creds.valid:
                                st.error("❌ Gmail token expired. Run Gmail watcher to re-authorize.")
                            else:
                                from src.utils.email_sender import send_email
                                result = send_email(email_to, email_subject, email_body)
                                # Gmail API returns dict with 'id' and 'threadId' on success
                                if result and result.get("id"):
                                    st.success(f"✅ Email sent to {email_to}! (ID: {result['id'][:12]}...)")
                                    st.session_state.show_email_form = False
                                    st.session_state.email_sent = True
                                else:
                                    st.error(f"❌ Failed to send email")
                    except ImportError as e:
                        st.warning(f"📧 Email module not available: {e}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    if st.session_state.email_sent:
        st.success("✅ Email sent successfully!")
        if st.button("📝 Send Another", key="send_another"):
            st.session_state.email_sent = False
            st.session_state.show_email_form = True
            st.rerun()

    st.divider()

    # Communication Summary
    st.subheader("📊 Communication Summary")

    # Get all communication files
    email_count = len(list(DONE_DIR.glob("EMAIL_*.md"))) if DONE_DIR.exists() else 0
    wa_count = len(list(DONE_DIR.glob("WA_*.md"))) if DONE_DIR.exists() else 0
    total = email_count + wa_count

    if total > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📧 Email", email_count)
        with col2:
            st.metric("💬 WhatsApp", wa_count)
        with col3:
            st.metric("📊 Total", total)
    else:
        st.info("No communication activity recorded yet")


def render_settings():
    """Render Settings section with system configuration."""
    st.header("⚙️ Settings")

    # General Settings
    st.subheader("🔧 General Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**System Settings**")
        dry_run = os.getenv("DRY_RUN", "false")
        poll_interval = os.getenv("POLL_INTERVAL", "60")
        claude_timeout = os.getenv("CLAUDE_TIMEOUT", "600")
        mcp_idle_timeout = os.getenv("MCP_IDLE_TIMEOUT", "30")

        st.write(f"**DRY_RUN Mode**: `{dry_run}` {'(Testing)' if dry_run == 'true' else '(Production)'}")
        st.write(f"**Poll Interval**: `{poll_interval}s` — How often watchers check")
        st.write(f"**Claude Timeout**: `{claude_timeout}s` — Max time for AI tasks")
        st.write(f"**MCP Idle Timeout**: `{mcp_idle_timeout}s` — Auto-stop containers")

    with col2:
        st.markdown("**Environment**")
        st.write(f"**Project Root**: `{PROJECT_ROOT.name}`")
        st.write(f"**Vault Path**: `{VAULT_PATH.name}`")
        st.write(f"**Python**: `{os.sys.version.split()[0]}`")

        # Check uv
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=5)
            uv_version = result.stdout.strip() if result.returncode == 0 else "Not found"
            st.write(f"**UV**: `{uv_version}`")
        except Exception:
            st.write("**UV**: `Not found`")

    st.divider()

    # Docker / Odoo Settings
    st.subheader("🐳 Docker — Odoo")

    try:
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                               capture_output=True, text=True, timeout=5)
        containers = result.stdout.strip().split("\n") if result.stdout.strip() else []

        odoo_containers = [c for c in containers if "odoo" in c.lower() or "postgres" in c.lower()]

        if odoo_containers:
            st.markdown('<p class="status-connected">● Running</p>', unsafe_allow_html=True)
            st.write(f"**Active Containers**: {len(odoo_containers)}")
            for container in odoo_containers:
                st.write(f"  - `{container}`")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Restart Odoo"):
                    st.info("Restart via: `docker-compose restart` in docker/odoo/")
            with col2:
                if st.button("⏹️ Stop Odoo"):
                    st.info("Stop via: `docker-compose down` in docker/odoo/")
            with col3:
                if st.button("🌐 Open Odoo Web"):
                    st.markdown(f"[Open Odoo]({ODOO_URL})")

        else:
            st.markdown('<p class="status-disconnected">● Not Running</p>', unsafe_allow_html=True)
            st.warning("Odoo containers are not running")

            if st.button("▶️ Start Odoo"):
                st.info("Start via: `docker-compose up -d` in docker/odoo/")

    except Exception as e:
        st.error(f"Docker not available: {e}")

    st.divider()

    # MCP Servers Status
    st.subheader("🔌 MCP Servers")

    mcp_status = get_mcp_server_status()

    status_table = []
    for server, configured in mcp_status.items():
        status_icon = "🟢" if configured else "🔴"
        status_text = "Configured" if configured else "Not Configured"
        status_table.append({
            "Server": server.title(),
            "Status": f"{status_icon} {status_text}",
            "Config File": ".mcp.json"
        })

    import pandas as pd
    df = pd.DataFrame(status_table)
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("📖 MCP Server Configuration"):
        st.markdown("""
        MCP servers are configured in `.mcp.json` at project root.

        **Available Servers**:
        - `fte-email`: Email sending via Gmail API
        - `fte-odoo`: Odoo accounting integration
        - `fte-facebook`: Facebook Page management
        - `fte-instagram`: Instagram content management
        - `fte-twitter`: Twitter/X automation (optional)
        - `fte-linkedin`: LinkedIn automation (optional)

        **Credentials**: Stored in `.env` file (never committed to git)
        """)

    st.divider()

    # Approval Rules
    st.subheader("🔐 Approval Rules")

    st.markdown("""
    Configure which actions require human approval before execution.

    **Current Rules** (from Company_Handbook.md):
    """)

    approval_rules = [
        ("Invoice Creation", "Auto-Approve", "Draft invoices are safe"),
        ("Invoice Reply Email", "Auto-Approve", "Confirmation emails are safe"),
        ("Payment Recording", "Require Approval", "Financial actions need review"),
        ("External Email Reply", "Require Approval", "Client communication needs review"),
        ("Social Media Post", "Require Approval", "Public content needs review"),
        ("Archive/No-Action", "Auto-Approve", "No external action taken")
    ]

    for action, rule, reason in approval_rules:
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.write(f"**{action}**")
        with col2:
            if rule == "Auto-Approve":
                st.markdown('<span class="status-connected">✓ Auto</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-warning">⚠ Manual</span>', unsafe_allow_html=True)
        with col3:
            st.caption(reason)

    st.info("💡 Approval rules are defined in `AI_Employee_Vault/Company_Handbook.md`")

    st.divider()

    # Logs & Audit
    st.subheader("📋 Logs & Audit")

    if LOGS_DIR.exists():
        log_files = list(LOGS_DIR.glob("*.json"))
        total_size = sum(f.stat().st_size for f in log_files) / (1024 * 1024)  # MB

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Log Files", len(log_files))
        with col2:
            st.metric("Total Size", f"{total_size:.2f} MB")
        with col3:
            retention_days = os.getenv("LOG_RETENTION_DAYS", "90")
            st.metric("Retention", f"{retention_days} days")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📂 View Logs"):
                st.info("Switch to Logs tab")
        with col2:
            if st.button("📥 Export Logs"):
                st.info("Export functionality coming soon")
        with col3:
            if st.button("🗑️ Clear Old Logs"):
                st.warning("This will delete logs older than retention period")

    else:
        st.info("No logs directory found")

    st.divider()

    # About
    st.subheader("ℹ️ About")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **FTE AI Employee Dashboard**

        - **Version**: Gold Tier v1.0
        - **Tier**: Autonomous Employee
        - **Model**: Claude Opus 4.6
        - **Framework**: Streamlit
        """)

    with col2:
        st.markdown("""
        **Features**:
        - Cross-domain integration
        - Odoo accounting
        - Social media management
        - Email & WhatsApp automation
        - CEO Briefing generation
        - Comprehensive audit logging
        """)


def render_logs():
    """Render comprehensive Activity Logs section."""
    st.header("📝 Activity Logs")

    if not LOGS_DIR.exists():
        st.info("No logs directory found")
        return

    # List log files
    log_files = sorted(LOGS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not log_files:
        st.info("No log files yet")
        return

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)

    total_logs = len(log_files)
    total_size = sum(f.stat().st_size for f in log_files) / 1024  # KB
    today = datetime.now().strftime("%Y-%m-%d")
    today_logs = [f for f in log_files if today in f.name]

    with col1:
        st.metric("Total Log Files", total_logs)
    with col2:
        st.metric("Today's Logs", len(today_logs))
    with col3:
        st.metric("Total Size", f"{total_size:.1f} KB")
    with col4:
        oldest = min(log_files, key=lambda x: x.stat().st_mtime)
        days_old = (datetime.now() - datetime.fromtimestamp(oldest.stat().st_mtime)).days
        st.metric("Oldest Log", f"{days_old} days")

    st.divider()

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        dates = [f.stem[:10] for f in log_files]
        unique_dates = sorted(set(dates), reverse=True)
        selected_date = st.selectbox("📅 Select Date", unique_dates)

    with col2:
        # Get action types from logs
        action_types = set()
        for log_file in log_files[:50]:  # Sample first 50 for performance
            try:
                data = json.loads(log_file.read_text())
                # Handle both array and single object formats
                entries = data if isinstance(data, list) else [data]
                for entry in entries:
                    if isinstance(entry, dict) and "action_type" in entry:
                        action_types.add(entry["action_type"])
            except Exception:
                pass

        action_filter = st.selectbox("🔍 Filter by Action", ["All"] + sorted(list(action_types)))

    with col3:
        limit = st.number_input("Show", min_value=5, max_value=100, value=20, step=5)

    # Show logs for selected date
    date_logs = [f for f in log_files if f.stem.startswith(selected_date)]

    if not date_logs:
        st.info(f"No logs found for {selected_date}")
        return

    st.subheader(f"Logs for {selected_date}")

    # Parse and display logs
    displayed = 0
    for log_file in date_logs:
        if displayed >= limit:
            break

        try:
            raw_data = json.loads(log_file.read_text())
            # Handle both array and single object formats
            entries = raw_data if isinstance(raw_data, list) else [raw_data]

            for data in entries:
                if displayed >= limit:
                    break
                if not isinstance(data, dict):
                    continue

                # Apply action filter
                if action_filter != "All" and data.get("action_type") != action_filter:
                    continue

                displayed += 1

                # Determine status color
                status = data.get("status", "unknown")
                if status == "success":
                    status_icon = "🟢"
                elif status == "error":
                    status_icon = "🔴"
                elif status == "pending":
                    status_icon = "🟡"
                else:
                    status_icon = "⚪"

                # Create expander title
                timestamp = data.get("timestamp", "")[:19].replace("T", " ")
                action = data.get("action_type", "unknown").replace("_", " ").title()
                source = data.get("source", "unknown")

                title = f"{status_icon} {timestamp} — {action} ({source})"

                with st.expander(title):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.markdown("**Details**")
                        st.write(f"**Action**: {data.get('action_type', 'N/A')}")
                        st.write(f"**Source**: {data.get('source', 'N/A')}")
                        st.write(f"**Status**: {data.get('status', 'N/A')}")
                        st.write(f"**Target**: {data.get('target_file', 'N/A')}")

                    with col2:
                        st.markdown("**Metadata**")
                        st.write(f"**Timestamp**: {data.get('timestamp', 'N/A')}")
                        st.write(f"**Duration**: {data.get('duration_ms', 'N/A')} ms")
                        st.write(f"**MCP Server**: {data.get('mcp_server', 'N/A')}")
                        st.write(f"**Workflow ID**: {data.get('workflow_id', 'N/A')}")

                    # Show full JSON in collapsed section
                    with st.expander("📄 View Full JSON"):
                        st.json(data)

        except Exception as e:
            st.error(f"Error reading {log_file.name}: {e}")

    if displayed == 0:
        st.info(f"No logs match the filter criteria")
    elif displayed < len(date_logs):
        st.info(f"Showing {displayed} of {len(date_logs)} logs. Increase limit to see more.")


def render_ceo_briefing():
    """Render CEO Briefing section."""
    st.header("📊 CEO Briefing")

    st.markdown("""
    Weekly business intelligence report synthesizing data from all integrated domains:
    Finance (Odoo), Social Media (Facebook, Instagram), and Communications (Email, WhatsApp).
    """)

    # Check if briefings exist
    if not BRIEFINGS_DIR.exists():
        st.warning("No briefings directory found. CEO Briefing has not been generated yet.")

        if st.button("📊 Generate CEO Briefing Now"):
            st.info("CEO Briefing generation requires the orchestrator to be running. Trigger via scheduled task or manual execution.")

        with st.expander("📖 How to Generate CEO Briefing"):
            st.markdown("""
            **Automatic Generation** (Recommended):
            - CEO Briefing is automatically generated every Sunday night at 11 PM
            - Scheduled via APScheduler in the orchestrator

            **Manual Generation**:
            ```bash
            # Trigger CEO Briefing generation
            uv run python -m src.main briefing
            ```

            **What's Included**:
            - Financial summary from Odoo (revenue, expenses, pending invoices)
            - Social media metrics (posts, engagement, reach)
            - Communication summary (emails, WhatsApp messages)
            - Action items and recommendations
            """)
        return

    # Get list of briefings
    briefings = sorted(BRIEFINGS_DIR.glob("CEO_Briefing_*.md"), reverse=True)

    if not briefings:
        st.warning("No CEO Briefings found yet.")
        return

    # Briefing selector
    col1, col2 = st.columns([3, 1])

    with col1:
        briefing_names = [f.name for f in briefings]
        selected_briefing = st.selectbox("📅 Select Briefing", briefing_names)

    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Load and display selected briefing
    selected_file = BRIEFINGS_DIR / selected_briefing

    try:
        content = selected_file.read_text(encoding="utf-8")

        # Display metadata
        file_date = datetime.fromtimestamp(selected_file.stat().st_mtime)
        st.caption(f"Generated: {file_date.strftime('%Y-%m-%d %H:%M:%S')}")

        st.divider()

        # Display briefing content (strip YAML frontmatter)
        display_content = content
        if display_content.strip().startswith("---"):
            parts = display_content.strip().split("---", 2)
            if len(parts) >= 3:
                display_content = parts[2].strip()
        st.markdown(display_content)

        st.divider()

        # Actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📥 Download as PDF"):
                try:
                    from fpdf import FPDF

                    pdf = FPDF()
                    pdf.set_auto_page_break(auto=True, margin=20)

                    # Use DejaVu font for Unicode support
                    dejavu_path = Path("/usr/share/fonts/truetype/dejavu")
                    if dejavu_path.exists() and (dejavu_path / "DejaVuSans.ttf").exists():
                        pdf.add_font("DejaVu", "", str(dejavu_path / "DejaVuSans.ttf"))
                        pdf.add_font("DejaVu", "B", str(dejavu_path / "DejaVuSans-Bold.ttf"))
                        pdf.add_font("DejaVu", "I", str(dejavu_path / "DejaVuSans.ttf"))
                        font_family = "DejaVu"
                    else:
                        font_family = "Helvetica"

                    def safe_text(text):
                        return text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2026", "...").replace("\u2022", "-")

                    pdf.add_page()

                    # Header
                    pdf.set_font(font_family, "B", 20)
                    pdf.set_text_color(30, 30, 60)
                    pdf.cell(0, 15, "CEO Briefing", new_x="LMARGIN", new_y="NEXT", align="C")
                    pdf.set_font(font_family, "", 11)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 8, f"Generated: {file_date.strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
                    pdf.ln(5)
                    pdf.set_draw_color(50, 50, 120)
                    pdf.set_line_width(0.5)
                    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                    pdf.ln(8)

                    # Parse markdown content
                    # Strip YAML frontmatter
                    pdf_content = content
                    if pdf_content.strip().startswith("---"):
                        parts = pdf_content.strip().split("---", 2)
                        if len(parts) >= 3:
                            pdf_content = parts[2]

                    for line in pdf_content.split("\n"):
                        s = line.strip()
                        if not s:
                            pdf.ln(3)
                            continue
                        s = safe_text(s)

                        if s.startswith("# "):
                            pdf.set_font(font_family, "B", 16)
                            pdf.set_text_color(30, 30, 60)
                            pdf.cell(0, 10, s[2:], new_x="LMARGIN", new_y="NEXT")
                        elif s.startswith("## "):
                            pdf.ln(3)
                            pdf.set_font(font_family, "B", 14)
                            pdf.set_text_color(40, 40, 100)
                            pdf.cell(0, 9, s[3:], new_x="LMARGIN", new_y="NEXT")
                        elif s.startswith("### "):
                            pdf.set_font(font_family, "B", 12)
                            pdf.set_text_color(60, 60, 120)
                            pdf.cell(0, 8, s[4:], new_x="LMARGIN", new_y="NEXT")
                        elif s.startswith("|") and s.endswith("|"):
                            cells = [c.strip() for c in s.split("|")[1:-1]]
                            if all(set(c) <= set("- :") for c in cells):
                                continue
                            num_cells = max(len(cells), 1)
                            col_width = 180 / num_cells
                            pdf.set_font(font_family, "", 9)
                            pdf.set_text_color(50, 50, 50)
                            for cell in cells:
                                bold = cell.startswith("**") and cell.endswith("**")
                                if bold:
                                    pdf.set_font(font_family, "B", 9)
                                    cell = cell.strip("*")
                                pdf.cell(col_width, 7, safe_text(cell[:40]), border=1, align="C")
                                if bold:
                                    pdf.set_font(font_family, "", 9)
                            pdf.ln()
                        elif s.startswith("- ") or s.startswith("* "):
                            pdf.set_font(font_family, "", 10)
                            pdf.set_text_color(50, 50, 50)
                            text = s[2:].replace("**", "")
                            pdf.cell(0, 6, safe_text(f"  {chr(8226)} {text}"), new_x="LMARGIN", new_y="NEXT")
                        elif len(s) > 2 and s[0].isdigit() and s[1] in ".)":
                            pdf.set_font(font_family, "", 10)
                            pdf.set_text_color(50, 50, 50)
                            pdf.cell(0, 6, safe_text(s), new_x="LMARGIN", new_y="NEXT")
                        elif s.startswith("_") and s.endswith("_"):
                            pdf.set_font(font_family, "I", 10)
                            pdf.set_text_color(100, 100, 100)
                            pdf.cell(0, 6, safe_text(s.strip("_")), new_x="LMARGIN", new_y="NEXT")
                        elif s.startswith("**") and s.endswith("**"):
                            pdf.set_font(font_family, "B", 11)
                            pdf.set_text_color(40, 40, 40)
                            pdf.cell(0, 6, safe_text(s.strip("*")), new_x="LMARGIN", new_y="NEXT")
                        else:
                            pdf.set_font(font_family, "", 10)
                            pdf.set_text_color(50, 50, 50)
                            clean = s.replace("**", "").replace("*", "")
                            pdf.cell(0, 6, safe_text(clean), new_x="LMARGIN", new_y="NEXT")

                    # Footer
                    pdf.ln(10)
                    pdf.set_draw_color(50, 50, 120)
                    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                    pdf.ln(5)
                    pdf.set_font(font_family, "I", 9)
                    pdf.set_text_color(130, 130, 130)
                    pdf.cell(0, 6, "Generated by FTE AI Employee Dashboard | Powered by Claude Opus 4.6", align="C")

                    # Download button
                    pdf_filename = selected_briefing.replace(".md", ".pdf")
                    pdf_bytes = bytes(pdf.output())
                    st.download_button(
                        label="💾 Save PDF",
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"PDF generation error: {e}")

        with col2:
            if st.button("📧 Email Briefing"):
                st.session_state.show_briefing_email = True

        with col3:
            if st.button("📊 Generate New Briefing"):
                try:
                    from src.utils.ceo_briefing import CEOBriefingGenerator
                    generator = CEOBriefingGenerator(vault_path=VAULT_PATH)
                    result_path = generator.generate()
                    if result_path and result_path.exists():
                        st.success(f"✅ New briefing generated: {result_path.name}")
                        st.rerun()
                    else:
                        st.warning("Briefing generation returned no result")
                except Exception as e:
                    st.error(f"Error generating briefing: {e}")

        # Email Briefing Form
        if st.session_state.get("show_briefing_email", False):
            with st.form("briefing_email_form"):
                st.markdown("### 📧 Email CEO Briefing")
                briefing_to = st.text_input("To", placeholder="ceo@company.com")
                send_briefing = st.form_submit_button("📨 Send Briefing", type="primary")
                cancel_briefing = st.form_submit_button("❌ Cancel")

                if cancel_briefing:
                    st.session_state.show_briefing_email = False
                    st.rerun()

                if send_briefing:
                    if not briefing_to:
                        st.error("❌ Please enter email address")
                    else:
                        try:
                            from google.oauth2.credentials import Credentials
                            from google.auth.transport.requests import Request

                            token_path = os.getenv("GMAIL_TOKEN_PATH", ".secrets/gmail_token.json")
                            token_file = Path(token_path)
                            if not token_file.exists():
                                st.error("❌ Gmail token not found. Authorize Gmail first.")
                            else:
                                creds = Credentials.from_authorized_user_file(str(token_file))
                                if creds and creds.expired and creds.refresh_token:
                                    creds.refresh(Request())
                                if not creds or not creds.valid:
                                    st.error("❌ Gmail token expired. Re-authorize Gmail.")
                                else:
                                    from src.utils.email_sender import send_email
                                    from fpdf import FPDF

                                    briefing_date = file_date.strftime("%B %d, %Y")
                                    subject = f"CEO Briefing - {briefing_date}"

                                    # Generate PDF attachment
                                    pdf = FPDF()
                                    pdf.set_auto_page_break(auto=True, margin=20)
                                    dejavu_p = Path("/usr/share/fonts/truetype/dejavu")
                                    if dejavu_p.exists() and (dejavu_p / "DejaVuSans.ttf").exists():
                                        pdf.add_font("DejaVu", "", str(dejavu_p / "DejaVuSans.ttf"))
                                        pdf.add_font("DejaVu", "B", str(dejavu_p / "DejaVuSans-Bold.ttf"))
                                        pdf.add_font("DejaVu", "I", str(dejavu_p / "DejaVuSans.ttf"))
                                        ff = "DejaVu"
                                    else:
                                        ff = "Helvetica"

                                    def _safe(t):
                                        return t.replace("\u2014", "-").replace("\u2013", "-")

                                    pdf_content = content
                                    if pdf_content.strip().startswith("---"):
                                        pp = pdf_content.strip().split("---", 2)
                                        if len(pp) >= 3:
                                            pdf_content = pp[2]

                                    pdf.add_page()
                                    pdf.set_font(ff, "B", 20); pdf.set_text_color(30, 30, 60)
                                    pdf.cell(0, 15, "CEO Briefing", new_x="LMARGIN", new_y="NEXT", align="C")
                                    pdf.set_font(ff, "", 11); pdf.set_text_color(100, 100, 100)
                                    pdf.cell(0, 8, f"Generated: {briefing_date}", new_x="LMARGIN", new_y="NEXT", align="C")
                                    pdf.ln(5); pdf.set_draw_color(50, 50, 120); pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(8)

                                    for ln in pdf_content.split("\n"):
                                        sl = ln.strip()
                                        if not sl:
                                            pdf.ln(3); continue
                                        sl = _safe(sl)
                                        if sl.startswith("# "):
                                            pdf.set_font(ff, "B", 16); pdf.set_text_color(30, 30, 60); pdf.cell(0, 10, sl[2:], new_x="LMARGIN", new_y="NEXT")
                                        elif sl.startswith("## "):
                                            pdf.ln(3); pdf.set_font(ff, "B", 14); pdf.set_text_color(40, 40, 100); pdf.cell(0, 9, sl[3:], new_x="LMARGIN", new_y="NEXT")
                                        elif sl.startswith("### "):
                                            pdf.set_font(ff, "B", 12); pdf.set_text_color(60, 60, 120); pdf.cell(0, 8, sl[4:], new_x="LMARGIN", new_y="NEXT")
                                        elif sl.startswith("|") and sl.endswith("|"):
                                            cells = [c.strip() for c in sl.split("|")[1:-1]]
                                            if all(set(c) <= set("- :") for c in cells): continue
                                            cw = 180 / max(len(cells), 1)
                                            pdf.set_font(ff, "", 9); pdf.set_text_color(50, 50, 50)
                                            for cl in cells:
                                                bd = cl.startswith("**") and cl.endswith("**")
                                                if bd: pdf.set_font(ff, "B", 9); cl = cl.strip("*")
                                                pdf.cell(cw, 7, _safe(cl[:40]), border=1, align="C")
                                                if bd: pdf.set_font(ff, "", 9)
                                            pdf.ln()
                                        elif sl.startswith("- ") or sl.startswith("* "):
                                            pdf.set_font(ff, "", 10); pdf.set_text_color(50, 50, 50)
                                            pdf.cell(0, 6, _safe(f"  {chr(8226)} {sl[2:].replace('**', '')}"), new_x="LMARGIN", new_y="NEXT")
                                        elif sl.startswith("_") and sl.endswith("_"):
                                            pdf.set_font(ff, "I", 10); pdf.set_text_color(100, 100, 100)
                                            pdf.cell(0, 6, _safe(sl.strip("_")), new_x="LMARGIN", new_y="NEXT")
                                        else:
                                            pdf.set_font(ff, "", 10); pdf.set_text_color(50, 50, 50)
                                            pdf.cell(0, 6, _safe(sl.replace("**", "").replace("*", "")), new_x="LMARGIN", new_y="NEXT")

                                    pdf.ln(10); pdf.set_draw_color(50, 50, 120); pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(5)
                                    pdf.set_font(ff, "I", 9); pdf.set_text_color(130, 130, 130)
                                    pdf.cell(0, 6, "Generated by FTE AI Employee Dashboard | Powered by Claude Opus 4.6", align="C")

                                    pdf_bytes = bytes(pdf.output())
                                    pdf_name = f"CEO_Briefing_{briefing_date.replace(' ', '_').replace(',', '')}.pdf"

                                    # Short professional email body
                                    email_body = f"""Hi,

Please find attached the CEO Briefing for {briefing_date}.

This report includes:
- Financial Summary
- Social Media Performance (Facebook, Instagram, LinkedIn)
- Communications Overview (Email, WhatsApp)
- Action Items & Recommendations

Best regards,
FTE AI Employee
Powered by Claude Opus 4.6"""

                                    result = send_email(
                                        briefing_to, subject, email_body,
                                        attachment=pdf_bytes, attachment_name=pdf_name
                                    )
                                    if result and result.get("id"):
                                        st.success(f"✅ Briefing emailed to {briefing_to}!")
                                        st.session_state.show_briefing_email = False
                                    else:
                                        st.error("❌ Failed to send email")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")

    except Exception as e:
        st.error(f"Error loading briefing: {e}")


# ==================== MAIN ====================

def render_sidebar():
    """Render sidebar navigation menu."""
    with st.sidebar:
        st.markdown("### 🤖 Navigation")
        st.markdown("---")

        # Navigation menu
        menu_items = [
            ("📊 Overview", "overview"),
            ("💰 Finance", "finance"),
            ("📱 Social Media", "social"),
            ("💬 Communications", "communications"),
            ("📊 CEO Briefing", "briefing"),
            ("⚙️ Settings", "settings"),
            ("📝 Logs", "logs"),
        ]

        # Initialize session state for selected page
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'overview'

        # Render menu buttons
        for label, page_id in menu_items:
            if st.button(label, key=f"nav_{page_id}", use_container_width=True):
                st.session_state.selected_page = page_id
                st.rerun()

        st.markdown("---")

        # Quick stats in sidebar
        stats = get_vault_stats()
        st.markdown("### 📊 Quick Stats")
        st.metric("Needs Action", stats["needs_action"])
        st.metric("Pending Approval", stats["pending_approval"])

        st.markdown("---")
        st.caption("FTE AI Employee v1.0")


def main():
    """Main dashboard application with sidebar navigation."""
    render_header()
    render_sidebar()

    # Get current page from session state
    current_page = st.session_state.get('selected_page', 'overview')

    # Render selected page
    if current_page == 'overview':
        render_overview()
    elif current_page == 'finance':
        render_finance()
    elif current_page == 'social':
        render_social_media()
    elif current_page == 'communications':
        render_communications()
    elif current_page == 'briefing':
        render_ceo_briefing()
    elif current_page == 'settings':
        render_settings()
    elif current_page == 'logs':
        render_logs()

    # Footer
    st.divider()
    st.caption("Powered by Claude Opus 4.6 & Streamlit")


if __name__ == "__main__":
    main()
