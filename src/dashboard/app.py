"""FTE AI Employee Dashboard — Streamlit application.

Real-time overview of AI employee activities: Finance, Social Media, Communications.
"""
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
DASHBOARD_FILE = VAULT_PATH / "Dashboard.md"
LOGS_DIR = PROJECT_ROOT / "AI_Employee_Vault" / "Logs"
PLANS_DIR = VAULT_PATH / "Plans"
DONE_DIR = VAULT_PATH / "Done"
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"

# Odoo config
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "fte-ai-employee")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")


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


def get_vault_stats() -> dict:
    """Get stats from vault files."""
    stats = {
        "needs_action": 0,
        "plans": 0,
        "done": 0,
        "logs_today": 0,
    }

    if NEEDS_ACTION_DIR.exists():
        stats["needs_action"] = len(list(NEEDS_ACTION_DIR.glob("*.md")))
    if PLANS_DIR.exists():
        stats["plans"] = len(list(PLANS_DIR.glob("*.md")))
    if DONE_DIR.exists():
        stats["done"] = len(list(DONE_DIR.glob("*.md")))
    if LOGS_DIR.exists():
        today = datetime.now().strftime("%Y-%m-%d")
        stats["logs_today"] = len([f for f in LOGS_DIR.glob("*.json") if today in f.name])

    return stats


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


def get_dashboard_content() -> str:
    """Read current Dashboard.md content."""
    if DASHBOARD_FILE.exists():
        return DASHBOARD_FILE.read_text()
    return ""


# ==================== UI COMPONENTS ====================

def render_header():
    """Render dashboard header."""
    st.set_page_config(page_title="FTE AI Employee Dashboard", page_icon="🤖", layout="wide")

    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
    }
    .main-header p {
        color: #a0c4e8;
        margin: 5px 0 0 0;
    }
    .stat-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2d5a87;
    }
    .status-connected { color: #28a745; }
    .status-disconnected { color: #dc3545; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header"><h1>🤖 FTE AI Employee Dashboard</h1><p>Real-time overview of autonomous AI employee activities</p></div>', unsafe_allow_html=True)


def render_overview():
    """Render Overview section."""
    st.header("📊 Overview")

    stats = get_vault_stats()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📥 Needs Action", stats["needs_action"])
    with col2:
        st.metric("📋 Active Plans", stats["plans"])
    with col3:
        st.metric("✅ Completed", stats["done"])
    with col4:
        st.metric("📝 Today's Logs", stats["logs_today"])

    st.subheader("Recent Activity")
    activities = get_recent_activity(5)
    if activities:
        for act in activities:
            st.write(f"- **{act.get('skill', 'N/A')}** — {act.get('status', 'N/A')} — {act.get('time', '')[:16]}")
    else:
        st.info("No recent activity")


def render_finance():
    """Render Finance section (Odoo)."""
    st.header("💰 Finance")

    # Connection status
    odoo_connected = False
    try:
        resp = requests.get(f"{ODOO_URL}/web/database/selector", timeout=5)
        odoo_connected = resp.status_code == 200
    except Exception:
        pass

    if odoo_connected:
        st.markdown('<p class="status-connected">● Odoo Connected</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-disconnected">● Odoo Disconnected</p>', unsafe_allow_html=True)

    if not odoo_connected:
        st.warning("Odoo is not running. Start Docker containers to view finance data.")
        return

    # Weekly summary
    with st.spinner("Loading weekly summary..."):
        summary = get_odoo_weekly_summary()

    if "error" in summary:
        st.error(f"Error: {summary['error']}")
    else:
        data = summary.get("data", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Weekly Revenue", f"PKR {data.get('total_revenue', 0):,.0f}")
        with col2:
            st.metric("Outstanding", f"PKR {data.get('outstanding_balance', 0):,.0f}")
        with col3:
            st.metric("Pending Invoices", data.get("pending_invoices_count", 0))

    # Recent invoices
    st.subheader("Recent Invoices")
    with st.spinner("Loading invoices..."):
        invoices = get_odoo_invoices(limit=10)

    if "error" in invoices:
        st.error(f"Error: {invoices['error']}")
    elif invoices.get("data"):
        import pandas as pd
        df = pd.DataFrame(invoices["data"])
        st.dataframe(
            df[["name", "partner_id", "amount_total", "state", "payment_state", "invoice_date_due"]],
            use_container_width=True
        )
    else:
        st.info("No invoices found")


def render_social_media():
    """Render Social Media section."""
    st.header("📱 Social Media")

    # Connection status indicators (mock for now - would use MCP tools)
    connections = {
        "Facebook": False,
        "Instagram": False,
        "Twitter/X": False,
        "LinkedIn": False,
    }

    # Check if MCP config exists
    mcp_file = PROJECT_ROOT / ".mcp.json"
    if mcp_file.exists():
        try:
            mcp_config = json.loads(mcp_file.read_text())
            # Check which servers are configured
            for server in mcp_config.get("mcpServers", {}).keys():
                if "facebook" in server.lower():
                    connections["Facebook"] = True
                if "instagram" in server.lower():
                    connections["Instagram"] = True
                if "twitter" in server.lower():
                    connections["Twitter/X"] = True
                if "linkedin" in server.lower():
                    connections["LinkedIn"] = True
        except Exception:
            pass

    cols = st.columns(4)
    platforms = list(connections.keys())
    for i, platform in enumerate(platforms):
        with cols[i]:
            status = "Connected" if connections[platform] else "Not Connected"
            color = "green" if connections[platform] else "red"
            st.markdown(f"**{platform}**: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)

    st.info("Social media MCP servers configured but not tested. Start the system to fetch real data.")

    # Placeholder for posts
    st.subheader("Recent Posts")
    st.write("No posts yet — configure social media MCPs to enable.")


def render_communications():
    """Render Communications section (Email + WhatsApp)."""
    st.header("💬 Communications")

    # Gmail status
    gmail_connected = False
    creds_path = PROJECT_ROOT / ".secrets" / "gmail_credentials.json"
    token_path = PROJECT_ROOT / ".secrets" / "gmail_token.json"

    if creds_path.exists() and token_path.exists():
        gmail_connected = True

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📧 Gmail")
        if gmail_connected:
            st.markdown('<p class="status-connected">● Connected</p>', unsafe_allow_html=True)
            stats = get_vault_stats()
            st.write(f"Emails processed: {stats['done']}")
        else:
            st.markdown('<p class="status-disconnected">● Not Connected</p>', unsafe_allow_html=True)
            st.info("Configure Gmail OAuth2 credentials in .secrets/")

    with col2:
        st.subheader("💬 WhatsApp")
        # Check WhatsApp config
        whatsapp_configured = False
        # Could check .env for WHATSAPP credentials
        if whatsapp_configured:
            st.markdown('<p class="status-connected">● Connected</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-disconnected">● Not Configured</p>', unsafe_allow_html=True)
            st.info("WhatsApp automation via Playwright — configure in .env")


def render_settings():
    """Render Settings section."""
    st.header("⚙️ Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("General")
        st.write(f"**Poll Interval**: {os.getenv('POLL_INTERVAL', '60')}s")
        st.write(f"**Claude Timeout**: {os.getenv('CLAUDE_TIMEOUT', '600')}s")
        st.write(f"**Dry Run**: {os.getenv('DRY_RUN', 'false')}")

    with col2:
        st.subheader("Docker")
        # Check Docker status
        try:
            result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                                   capture_output=True, text=True, timeout=5)
            containers = result.stdout.strip().split("\n") if result.stdout.strip() else []
            st.write(f"**Running Containers**: {len(containers)}")
            for c in containers[:5]:
                st.write(f"  - {c}")
        except Exception:
            st.write("**Docker**: Not available")


def render_logs():
    """Render Logs section."""
    st.header("📝 Activity Logs")

    if not LOGS_DIR.exists():
        st.info("No logs directory found")
        return

    # List log files
    log_files = sorted(LOGS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not log_files:
        st.info("No log files yet")
        return

    # Date filter
    dates = [f.stem[:10] for f in log_files]
    unique_dates = sorted(set(dates), reverse=True)

    selected_date = st.selectbox("Select Date", unique_dates)

    # Show logs for date
    date_logs = [f for f in log_files if f.stem.startswith(selected_date)]

    for log_file in date_logs[:10]:
        try:
            data = json.loads(log_file.read_text())
            with st.expander(f"📄 {log_file.name}"):
                st.json(data)
        except Exception as e:
            st.error(f"Error reading {log_file.name}: {e}")


# ==================== MAIN ====================

def main():
    render_overview()

    # Tabs for sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Finance",
        "📱 Social Media",
        "💬 Communications",
        "⚙️ Settings",
        "📝 Logs"
    ])

    with tab1:
        render_finance()

    with tab2:
        render_social_media()

    with tab3:
        render_communications()

    with tab4:
        render_settings()

    with tab5:
        render_logs()


if __name__ == "__main__":
    main()
