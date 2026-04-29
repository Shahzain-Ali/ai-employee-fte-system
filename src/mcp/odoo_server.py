"""MCP Server: fte-odoo — Odoo accounting via JSON-RPC.

Auto-manages Docker containers: starts Odoo+PostgreSQL on first call,
stops them when MCP server shuts down (via idle timeout or clean exit).
"""
import os
import sys
import json
import time
import atexit
import logging
import signal
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [fte-odoo] %(message)s")
logger = logging.getLogger("fte-odoo")

mcp = FastMCP("fte-odoo")

# Odoo connection config
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "fte-ai-employee")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

# Docker compose file path
COMPOSE_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "docker-compose.yml"

_uid_cache: int | None = None
_docker_started_by_us: bool = False


def _update_activity() -> None:
    """Log that an MCP tool was called (for debugging)."""
    logger.debug("MCP tool called at %s", datetime.now(timezone.utc).isoformat())


def _is_odoo_reachable() -> bool:
    """Check if Odoo is responding on its URL."""
    try:
        resp = requests.get(f"{ODOO_URL}/web/database/selector", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def _ensure_odoo_running() -> None:
    """Start Odoo Docker containers if not already running."""
    global _docker_started_by_us

    if _is_odoo_reachable():
        return

    logger.info("Odoo not reachable — starting Docker containers...")
    try:
        subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "start"],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        # Containers may not exist yet, try 'up'
        subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d"],
            capture_output=True, text=True, timeout=60,
        )

    # Wait for Odoo to be ready (max 60 seconds)
    for i in range(30):
        if _is_odoo_reachable():
            logger.info("Odoo is ready (took ~%ds)", (i + 1) * 2)
            _docker_started_by_us = True
            return
        time.sleep(2)

    raise ConnectionError("Odoo containers started but not responding after 60s")


def _stop_odoo_containers() -> None:
    """Stop Odoo Docker containers if we started them."""
    if _docker_started_by_us:
        logger.info("Stopping Odoo Docker containers (auto-cleanup)...")
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(COMPOSE_FILE), "stop"],
                capture_output=True, text=True, timeout=30,
            )
            logger.info("Odoo containers stopped")
        except Exception as e:
            logger.warning("Failed to stop containers: %s", e)


# Auto-stop containers when MCP server exits
atexit.register(_stop_odoo_containers)


def _signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received signal %d — shutting down...", signum)
    _stop_odoo_containers()
    sys.exit(0)


def _odoo_jsonrpc(service: str, method: str, args: list) -> dict:
    """Make a JSON-RPC call to Odoo. Auto-starts containers if needed.

    Args:
        service: Odoo service (common, object, db).
        method: RPC method name.
        args: Method arguments.

    Returns:
        Result from Odoo.

    Raises:
        ConnectionError: If Odoo is unreachable.
        RuntimeError: If Odoo returns an error.
    """
    _ensure_odoo_running()

    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": service,
            "method": method,
            "args": args,
        },
        "id": 1,
    }
    try:
        resp = requests.post(f"{ODOO_URL}/jsonrpc", json=payload, timeout=30)
        resp.raise_for_status()
    except requests.ConnectionError:
        raise ConnectionError(f"Cannot connect to Odoo at {ODOO_URL}")
    except requests.Timeout:
        raise TimeoutError(f"Odoo request timed out at {ODOO_URL}")

    data = resp.json()
    if "error" in data:
        err = data["error"]
        msg = err.get("data", {}).get("message", str(err))
        raise RuntimeError(f"Odoo error: {msg}")

    return data.get("result")


def _authenticate() -> int:
    """Authenticate with Odoo and return uid. Caches result."""
    global _uid_cache
    if _uid_cache is not None:
        return _uid_cache

    uid = _odoo_jsonrpc("common", "authenticate",
                        [ODOO_DB, ODOO_USER, ODOO_PASSWORD, {}])
    if not uid:
        raise RuntimeError("Odoo authentication failed — check credentials")
    _uid_cache = uid
    logger.info("Authenticated with Odoo (uid=%d)", uid)
    return uid


def _execute_kw(model: str, method: str, args: list, kwargs: dict | None = None):
    """Execute an Odoo model method via JSON-RPC.

    Args:
        model: Odoo model name (e.g., 'account.move').
        method: Model method (e.g., 'create', 'search_read').
        args: Positional arguments for the method.
        kwargs: Keyword arguments for the method.

    Returns:
        Result from Odoo.
    """
    uid = _authenticate()
    kw = kwargs or {}
    return _odoo_jsonrpc("object", "execute_kw",
                         [ODOO_DB, uid, ODOO_PASSWORD, model, method, args, kw])


def _find_or_create_partner(name: str) -> int:
    """Find a partner by name, or create a new one.

    Args:
        name: Partner/client name.

    Returns:
        Partner ID in Odoo.
    """
    partners = _execute_kw("res.partner", "search_read",
                           [[["name", "=", name]]],
                           {"fields": ["id"], "limit": 1})
    if partners:
        return partners[0]["id"]

    # Create new partner
    partner_id = _execute_kw("res.partner", "create", [{"name": name}])
    logger.info("Created partner: %s (id=%d)", name, partner_id)
    return partner_id


@mcp.tool()
def create_invoice(partner_name: str, lines: list[dict], due_date: str = "") -> str:
    """Create a new customer invoice in Odoo.

    Args:
        partner_name: Client/partner name (will be matched or created).
        lines: Invoice line items, each with 'description' and 'price_unit', optional 'quantity'.
        due_date: Due date in YYYY-MM-DD format (optional).
    """
    _update_activity()
    try:
        partner_id = _find_or_create_partner(partner_name)

        invoice_lines = []
        for line in lines:
            invoice_lines.append((0, 0, {
                "name": line["description"],
                "quantity": line.get("quantity", 1),
                "price_unit": line["price_unit"],
            }))

        vals = {
            "move_type": "out_invoice",
            "partner_id": partner_id,
            "invoice_line_ids": invoice_lines,
        }
        if due_date:
            vals["invoice_date_due"] = due_date

        invoice_id = _execute_kw("account.move", "create", [vals])

        # Read back to get total
        invoice = _execute_kw("account.move", "read", [[invoice_id]],
                              {"fields": ["name", "amount_total", "state"]})
        inv = invoice[0] if invoice else {}

        return (f"Invoice created: ID={invoice_id}, Partner={partner_name}, "
                f"Total={inv.get('amount_total', 'N/A')}, Status=Draft")
    except Exception as e:
        logger.error("create_invoice failed: %s", e)
        return f"Error creating invoice: {e}"


@mcp.tool()
def get_invoice_pdf(invoice_id: int) -> str:
    """Download invoice PDF from Odoo and return the local file path.

    Args:
        invoice_id: Odoo invoice ID (account.move).

    Returns:
        Local file path where PDF is saved, or error message.
    """
    _update_activity()
    try:
        uid = _authenticate()

        # Get invoice name for filename
        invoice = _execute_kw("account.move", "read", [[invoice_id]],
                              {"fields": ["name", "partner_id", "amount_total"]})
        if not invoice:
            return f"Error: Invoice ID {invoice_id} not found"

        inv = invoice[0]
        raw_name = inv.get("name")
        inv_name = (raw_name if isinstance(raw_name, str) else f"INV-{invoice_id}").replace("/", "-")

        # Confirm draft invoice so it gets a proper number and PDF can generate
        state = inv.get("state", "draft")
        if state == "draft":
            _execute_kw("account.move", "action_post", [[invoice_id]])
            # Re-read to get the assigned invoice number
            invoice = _execute_kw("account.move", "read", [[invoice_id]],
                                  {"fields": ["name"]})
            if invoice:
                new_name = invoice[0].get("name")
                if isinstance(new_name, str):
                    inv_name = new_name.replace("/", "-")

        # Download PDF via Odoo report endpoint
        session = requests.Session()
        # Login to get session cookie
        login_resp = session.post(f"{ODOO_URL}/web/session/authenticate", json={
            "jsonrpc": "2.0",
            "params": {
                "db": ODOO_DB,
                "login": ODOO_USER,
                "password": ODOO_PASSWORD,
            }
        }, timeout=10)

        if login_resp.status_code != 200:
            return f"Error: Could not authenticate with Odoo web"

        # Download PDF report
        pdf_url = f"{ODOO_URL}/report/pdf/account.report_invoice/{invoice_id}"
        pdf_resp = session.get(pdf_url, timeout=30)

        if pdf_resp.status_code != 200:
            return f"Error: Could not download PDF (status {pdf_resp.status_code})"

        # Save to temp directory
        import tempfile
        pdf_dir = Path(tempfile.gettempdir()) / "fte_invoices"
        pdf_dir.mkdir(exist_ok=True)
        pdf_path = pdf_dir / f"{inv_name}.pdf"
        pdf_path.write_bytes(pdf_resp.content)

        logger.info("Invoice PDF saved: %s (%d bytes)", pdf_path, len(pdf_resp.content))
        return str(pdf_path)
    except Exception as e:
        logger.error("get_invoice_pdf failed: %s", e)
        return f"Error downloading invoice PDF: {e}"


@mcp.tool()
def get_invoices(status: str = "all", limit: int = 20) -> str:
    """List invoices from Odoo with optional status filter.

    Args:
        status: Filter by invoice status (draft, posted, paid, all).
        limit: Maximum number of invoices to return.
    """
    _update_activity()
    try:
        domain = [["move_type", "=", "out_invoice"]]
        if status == "draft":
            domain.append(["state", "=", "draft"])
        elif status == "posted":
            domain.append(["state", "=", "posted"])
        elif status == "paid":
            domain.append(["payment_state", "=", "paid"])

        invoices = _execute_kw("account.move", "search_read", [domain], {
            "fields": ["id", "name", "partner_id", "amount_total",
                        "state", "payment_state", "invoice_date", "invoice_date_due"],
            "limit": limit,
            "order": "create_date desc",
        })

        results = []
        for inv in invoices:
            results.append({
                "id": inv["id"],
                "number": inv.get("name", ""),
                "partner": inv.get("partner_id", [None, ""])[1] if isinstance(inv.get("partner_id"), list) else str(inv.get("partner_id", "")),
                "amount": inv.get("amount_total", 0),
                "status": inv.get("state", ""),
                "payment_status": inv.get("payment_state", ""),
                "date": inv.get("invoice_date", ""),
                "due_date": inv.get("invoice_date_due", ""),
            })

        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        logger.error("get_invoices failed: %s", e)
        return f"Error listing invoices: {e}"


@mcp.tool()
def mark_payment_received(invoice_id: int, amount: float = 0, payment_date: str = "") -> str:
    """Record payment received for an invoice.

    Args:
        invoice_id: Odoo invoice ID.
        amount: Payment amount (defaults to full invoice amount if 0).
        payment_date: Payment date YYYY-MM-DD (defaults to today).
    """
    _update_activity()
    try:
        # Read invoice to get amount if not specified
        invoices = _execute_kw("account.move", "read", [[invoice_id]],
                               {"fields": ["amount_total", "state", "name"]})
        if not invoices:
            return f"Error: Invoice {invoice_id} not found"

        inv = invoices[0]
        pay_amount = amount if amount > 0 else inv.get("amount_total", 0)
        pay_date = payment_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Register payment via account.payment.register wizard
        ctx = {"active_model": "account.move", "active_ids": [invoice_id]}
        wizard_id = _odoo_jsonrpc("object", "execute_kw", [
            ODOO_DB, _authenticate(), ODOO_PASSWORD,
            "account.payment.register", "create",
            [{"amount": pay_amount, "payment_date": pay_date}],
            {"context": ctx},
        ])

        _odoo_jsonrpc("object", "execute_kw", [
            ODOO_DB, _authenticate(), ODOO_PASSWORD,
            "account.payment.register", "action_create_payments",
            [[wizard_id]],
            {"context": ctx},
        ])

        return (f"Payment recorded: Invoice {inv.get('name', invoice_id)} "
                f"marked as Paid. Amount={pay_amount}")
    except Exception as e:
        logger.error("mark_payment_received failed: %s", e)
        return f"Error recording payment: {e}"


@mcp.tool()
def get_weekly_summary(week_start: str = "") -> str:
    """Get financial summary for the current or specified week.

    Args:
        week_start: Week start date YYYY-MM-DD (defaults to current week's Monday).
    """
    _update_activity()
    try:
        if week_start:
            start = datetime.strptime(week_start, "%Y-%m-%d").date()
        else:
            today = datetime.now(timezone.utc).date()
            start = today - timedelta(days=today.weekday())  # Monday

        end = start + timedelta(days=6)  # Sunday

        # Revenue: paid invoices this week
        paid = _execute_kw("account.move", "search_read", [[
            ["move_type", "=", "out_invoice"],
            ["payment_state", "=", "paid"],
            ["invoice_date", ">=", str(start)],
            ["invoice_date", "<=", str(end)],
        ]], {"fields": ["amount_total"]})
        total_revenue = sum(inv.get("amount_total", 0) for inv in paid)

        # Pending invoices
        pending = _execute_kw("account.move", "search_read", [[
            ["move_type", "=", "out_invoice"],
            ["payment_state", "!=", "paid"],
            ["state", "=", "posted"],
        ]], {"fields": ["amount_total"]})
        pending_count = len(pending)
        outstanding = sum(inv.get("amount_total", 0) for inv in pending)

        # Expenses this week
        expenses = _execute_kw("hr.expense", "search_read", [[
            ["date", ">=", str(start)],
            ["date", "<=", str(end)],
        ]], {"fields": ["total_amount"]})
        total_expenses = sum(exp.get("total_amount", 0) for exp in expenses)

        summary = {
            "week_start": str(start),
            "week_end": str(end),
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "pending_invoices_count": pending_count,
            "outstanding_balance": outstanding,
        }

        return json.dumps(summary, indent=2, default=str)
    except Exception as e:
        logger.error("get_weekly_summary failed: %s", e)
        return f"Error getting weekly summary: {e}"


@mcp.tool()
def get_expenses(limit: int = 20) -> str:
    """List expenses from Odoo.

    Args:
        limit: Maximum number of expenses to return.
    """
    _update_activity()
    try:
        expenses = _execute_kw("hr.expense", "search_read", [[]], {
            "fields": ["id", "name", "total_amount", "date", "state"],
            "limit": limit,
            "order": "date desc",
        })

        results = []
        for exp in expenses:
            results.append({
                "id": exp["id"],
                "description": exp.get("name", ""),
                "amount": exp.get("total_amount", 0),
                "date": exp.get("date", ""),
                "status": exp.get("state", ""),
            })

        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        logger.error("get_expenses failed: %s", e)
        return f"Error listing expenses: {e}"


@mcp.tool()
def create_expense(description: str, amount: float, category: str = "", date: str = "") -> str:
    """Record a new expense in Odoo.

    Args:
        description: Expense description.
        amount: Expense amount.
        category: Expense category (e.g., 'Office Supplies', 'Travel').
        date: Expense date YYYY-MM-DD (defaults to today).
    """
    _update_activity()
    try:
        vals = {
            "name": description,
            "total_amount_currency": amount,
            "date": date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }

        expense_id = _execute_kw("hr.expense", "create", [vals])

        return f"Expense created: ID={expense_id}, Amount={amount}, Category={category or 'General'}"
    except Exception as e:
        logger.error("create_expense failed: %s", e)
        return f"Error creating expense: {e}"


@mcp.tool()
def delete_invoice(invoice_id: int) -> str:
    """Delete an invoice from Odoo by ID.

    Posted invoices are first reset to draft, then permanently deleted.

    Args:
        invoice_id: The numeric Odoo invoice ID to delete.
    """
    _update_activity()
    try:
        _ensure_odoo_running()

        # Fetch invoice to confirm it exists
        invoices = _execute_kw("account.move", "read", [[invoice_id]],
                               {"fields": ["name", "partner_id", "state", "amount_total"]})
        if not invoices:
            return f"Invoice ID={invoice_id} not found."

        inv = invoices[0]
        name = inv.get("name") or f"ID={invoice_id}"
        partner = inv.get("partner_id", [None, "Unknown"])[1]
        state = inv.get("state", "")

        # Posted invoices must be reset to draft before deletion
        if state == "posted":
            _execute_kw("account.move", "button_draft", [[invoice_id]])
            logger.info("Reset invoice %s to draft for deletion", name)

        # Permanently delete
        _execute_kw("account.move", "unlink", [[invoice_id]])
        logger.info("Deleted invoice %s (partner: %s)", name, partner)

        return f"Invoice {name} (partner: {partner}) permanently deleted from Odoo."

    except Exception as e:
        logger.error("delete_invoice failed: %s", e)
        return f"Error deleting invoice: {e}"


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    mcp.run(transport="stdio")
