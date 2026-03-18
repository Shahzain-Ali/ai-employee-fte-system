"""CEO Briefing generator — weekly business intelligence report."""
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

from src.utils.logger import AuditLogger, LogEntry

logger = logging.getLogger(__name__)


class CEOBriefingGenerator:
    """Generates weekly CEO Briefing by collecting data from all domains.

    Data sources: Odoo (financials), Facebook (social), Instagram (social),
    Gmail (vault file counts), WhatsApp (vault file counts).

    Handles missing data sources gracefully — includes available data
    and notes unavailable domains.

    Args:
        vault_path: Root path of the Obsidian vault.
    """

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self._audit = AuditLogger(vault_path=vault_path)

    def generate(self, week_start: str = "", week_end: str = "") -> Path:
        """Generate the weekly CEO Briefing.

        Args:
            week_start: Start date (YYYY-MM-DD). Defaults to last Monday.
            week_end: End date (YYYY-MM-DD). Defaults to last Sunday.

        Returns:
            Path to the generated briefing file.
        """
        today = datetime.now(timezone.utc).date()

        if week_start:
            start = datetime.strptime(week_start, "%Y-%m-%d").date()
        else:
            # Last Monday
            start = today - timedelta(days=today.weekday() + 7)

        if week_end:
            end = datetime.strptime(week_end, "%Y-%m-%d").date()
        else:
            end = start + timedelta(days=6)

        data_sources = []
        missing_sources = []

        # Collect data from each domain
        odoo_data = self._get_odoo_data(start, end)
        if odoo_data:
            data_sources.append("odoo")
        else:
            missing_sources.append("odoo")

        fb_data = self._get_facebook_data()
        if fb_data:
            data_sources.append("facebook")
        else:
            missing_sources.append("facebook")

        ig_data = self._get_instagram_data()
        if ig_data:
            data_sources.append("instagram")
        else:
            missing_sources.append("instagram")

        tw_data = self._get_twitter_data()
        if tw_data:
            data_sources.append("twitter")
        else:
            missing_sources.append("twitter")

        li_data = self._get_linkedin_data()
        if li_data:
            data_sources.append("linkedin")
        else:
            missing_sources.append("linkedin")

        comm_data = self._get_communication_data(start, end)
        if comm_data.get("emails_processed", 0) > 0 or comm_data.get("whatsapp_messages", 0) > 0:
            if comm_data.get("emails_processed", 0) > 0:
                data_sources.append("gmail")
            if comm_data.get("whatsapp_messages", 0) > 0:
                data_sources.append("whatsapp")
        if "gmail" not in data_sources:
            missing_sources.append("gmail")
        if "whatsapp" not in data_sources:
            missing_sources.append("whatsapp")

        # Render briefing
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        briefing = self._render_briefing(
            start, end, now, data_sources, missing_sources,
            odoo_data, fb_data, ig_data, tw_data, li_data, comm_data,
        )

        # Save briefing
        briefings_dir = self.vault_path / "Briefings"
        briefings_dir.mkdir(exist_ok=True)
        filename = f"CEO_Briefing_{end}.md"
        briefing_path = briefings_dir / filename
        briefing_path.write_text(briefing, encoding="utf-8")

        self._audit.log(LogEntry(
            action_type="ceo_briefing_generated",
            source="ceo_briefing",
            status="success",
            target_file=f"Briefings/{filename}",
            details={
                "week_start": str(start),
                "week_end": str(end),
                "data_sources": data_sources,
                "missing_sources": missing_sources,
            },
        ))

        logger.info("CEO Briefing generated: %s", filename)

        # Optionally email the briefing
        self._email_briefing(briefing_path)

        return briefing_path

    def _get_odoo_data(self, start, end) -> dict | None:
        """Collect financial data from Odoo via MCP server functions.

        Quick-checks if Odoo is reachable before attempting full connection.
        Skips if Docker is not running to avoid 60s timeout.
        """
        try:
            import requests
            odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
            try:
                requests.get(f"{odoo_url}/web/database/selector", timeout=3)
            except Exception:
                logger.info("Odoo not reachable — skipping financial data")
                return None

            from src.mcp.odoo_server import _ensure_odoo_running, _authenticate, _execute_kw

            _ensure_odoo_running()
            _authenticate()

            # Revenue (paid invoices this week)
            paid = _execute_kw("account.move", "search_read", [[
                ["move_type", "=", "out_invoice"],
                ["payment_state", "=", "paid"],
                ["invoice_date", ">=", str(start)],
                ["invoice_date", "<=", str(end)],
            ]], {"fields": ["amount_total"]}) or []
            revenue = sum(i.get("amount_total", 0) for i in paid)

            # Pending invoices
            pending = _execute_kw("account.move", "search_read", [[
                ["move_type", "=", "out_invoice"],
                ["payment_state", "!=", "paid"],
                ["state", "=", "posted"],
            ]], {"fields": ["amount_total"]}) or []

            # Expenses (may not be installed)
            total_expenses = 0
            try:
                expenses = _execute_kw("hr.expense", "search_read", [[
                    ["date", ">=", str(start)],
                    ["date", "<=", str(end)],
                ]], {"fields": ["total_amount"]}) or []
                total_expenses = sum(e.get("total_amount", 0) for e in expenses)
            except RuntimeError:
                logger.info("hr.expense module not available — expenses set to 0")

            return {
                "revenue": revenue,
                "pending_count": len(pending),
                "pending_amount": sum(i.get("amount_total", 0) for i in pending),
                "expenses": total_expenses,
            }
        except Exception as e:
            logger.warning("Failed to get Odoo data for briefing: %s", e)
            return None

    def _get_facebook_data(self) -> dict | None:
        """Collect Facebook metrics via Meta Graph API (real-time)."""
        try:
            import requests
            token = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
            page_id = os.getenv("FB_PAGE_ID", "")
            api_ver = os.getenv("META_API_VERSION", "v25.0")
            if not token or not page_id:
                return None

            resp = requests.get(
                f"https://graph.facebook.com/{api_ver}/{page_id}",
                params={"fields": "name,followers_count,fan_count", "access_token": token},
                timeout=10,
            )
            page_data = resp.json() if resp.status_code == 200 else {}

            posts_resp = requests.get(
                f"https://graph.facebook.com/{api_ver}/{page_id}/posts",
                params={"fields": "message,created_time", "limit": 5, "access_token": token},
                timeout=10,
            )
            posts = posts_resp.json().get("data", []) if posts_resp.status_code == 200 else []

            return {
                "page_name": page_data.get("name", "Unknown"),
                "followers": page_data.get("followers_count", page_data.get("fan_count", 0)),
                "post_count": len(posts),
                "engagement": f"{len(posts)} recent posts",
                "last_post": posts[0].get("message", "")[:50] + "..." if posts else "No posts",
            }
        except Exception as e:
            logger.warning("Failed to get Facebook API data: %s", e)
            return None

    def _get_instagram_data(self) -> dict | None:
        """Collect Instagram metrics via Meta Graph API (real-time)."""
        try:
            import requests
            token = os.getenv("IG_ACCESS_TOKEN", "")
            ig_id = os.getenv("IG_USER_ID", "")
            api_ver = os.getenv("META_API_VERSION", "v25.0")
            if not token or not ig_id:
                return None

            resp = requests.get(
                f"https://graph.facebook.com/{api_ver}/{ig_id}",
                params={"fields": "username,followers_count,media_count", "access_token": token},
                timeout=10,
            )
            ig_data = resp.json() if resp.status_code == 200 else {}

            media_resp = requests.get(
                f"https://graph.facebook.com/{api_ver}/{ig_id}/media",
                params={"fields": "caption,timestamp,like_count", "limit": 5, "access_token": token},
                timeout=10,
            )
            media = media_resp.json().get("data", []) if media_resp.status_code == 200 else []

            return {
                "username": ig_data.get("username", "Unknown"),
                "followers": ig_data.get("followers_count", 0),
                "post_count": ig_data.get("media_count", 0),
                "engagement": f"{len(media)} recent posts",
                "last_post": media[0].get("caption", "")[:50] + "..." if media else "No posts",
            }
        except Exception as e:
            logger.warning("Failed to get Instagram API data: %s", e)
            return None

    def _get_twitter_data(self) -> dict | None:
        """Collect Twitter/X metrics from environment check."""
        try:
            api_key = os.getenv("TWITTER_API_KEY", "")
            api_secret = os.getenv("TWITTER_API_SECRET", "")
            if not api_key or not api_secret:
                return None

            # Count vault posts as fallback (Twitter API v2 free tier is limited)
            done = self.vault_path / "Done"
            tw_count = 0
            if done.exists():
                tw_count = sum(1 for f in done.iterdir()
                               if f.name.startswith("TW_") or f.name.startswith("SUMMARY_TW_"))

            return {
                "post_count": tw_count,
                "engagement": "API connected",
                "last_post": "See vault",
            }
        except Exception:
            return None

    def _get_linkedin_data(self) -> dict | None:
        """Collect LinkedIn metrics via Official API (real-time)."""
        try:
            import requests
            token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
            person_urn = os.getenv("LINKEDIN_PERSON_URN", "")
            if not token or not person_urn:
                return None

            # Get profile info
            resp = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            profile = resp.json() if resp.status_code == 200 else {}

            # Count vault posts
            done = self.vault_path / "Done"
            li_count = 0
            if done.exists():
                li_count = sum(1 for f in done.iterdir()
                               if f.name.startswith("LI_") or f.name.startswith("SUMMARY_LI_"))

            return {
                "name": profile.get("name", "Connected"),
                "post_count": li_count,
                "engagement": "API connected",
                "last_post": "See vault",
            }
        except Exception as e:
            logger.warning("Failed to get LinkedIn API data: %s", e)
            return None

    def _get_communication_data(self, start, end) -> dict:
        """Count email and WhatsApp files in vault Done/ for the week."""
        done = self.vault_path / "Done"
        if not done.exists():
            return {"emails_processed": 0, "whatsapp_messages": 0, "pending_responses": 0}

        emails = 0
        whatsapp = 0
        for f in done.iterdir():
            if not f.is_file():
                continue
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).date()
                if start <= mtime <= end:
                    if f.name.startswith("EMAIL_"):
                        emails += 1
                    elif f.name.startswith("WA_"):
                        whatsapp += 1
            except OSError:
                continue

        # Pending responses (in Needs_Action + Pending_Approval)
        pending = 0
        for folder in ["Needs_Action", "Pending_Approval"]:
            d = self.vault_path / folder
            if d.exists():
                pending += sum(1 for f in d.iterdir() if f.is_file())

        return {
            "emails_processed": emails,
            "whatsapp_messages": whatsapp,
            "pending_responses": pending,
        }

    def _render_briefing(self, start, end, generated_at, data_sources,
                         missing_sources, odoo, fb, ig, tw, li, comm) -> str:
        """Render the CEO Briefing markdown document."""
        missing_yaml = f"[{', '.join(missing_sources)}]" if missing_sources else "[]"
        sources_yaml = f"[{', '.join(data_sources)}]"

        start_str = start.strftime("%b %d")
        end_str = end.strftime("%b %d, %Y")

        # Financial section
        if odoo:
            net = odoo["revenue"] - odoo["expenses"]
            financial = f"""## Financial Summary (Odoo)

| Metric | Value |
|--------|-------|
| Revenue | PKR {odoo['revenue']:,.0f} |
| Pending Invoices | {odoo['pending_count']} (PKR {odoo['pending_amount']:,.0f}) |
| Expenses | PKR {odoo['expenses']:,.0f} |
| Net Profit | PKR {net:,.0f} |"""
        else:
            financial = "## Financial Summary (Odoo)\n\n_Odoo data unavailable this week._"

        # Social media section
        social_parts = []

        if fb:
            social_parts.append(f"""### Facebook
- **Page:** {fb.get('page_name', 'Unknown')}
- **Followers:** {fb.get('followers', 0):,}
- **Recent Posts:** {fb.get('post_count', 0)}
- **Last Post:** {fb.get('last_post', 'N/A')}""")

        if ig:
            social_parts.append(f"""### Instagram
- **Account:** @{ig.get('username', 'Unknown')}
- **Followers:** {ig.get('followers', 0):,}
- **Total Posts:** {ig.get('post_count', 0)}
- **Last Post:** {ig.get('last_post', 'N/A')}""")

        if li:
            social_parts.append(f"""### LinkedIn
- **Profile:** {li.get('name', 'Connected')}
- **Posts This Week:** {li.get('post_count', 0)}
- **Status:** {li.get('engagement', 'N/A')}""")

        if tw:
            social_parts.append(f"""### Twitter/X
- **Posts This Week:** {tw.get('post_count', 0)}
- **Status:** {tw.get('engagement', 'N/A')}""")

        if social_parts:
            social = "## Social Media\n\n" + "\n\n".join(social_parts)
        else:
            social = "## Social Media\n\n_No social media platforms connected._"

        # Communications section
        communications = f"""## Communications (Gmail + WhatsApp)

- Emails processed: {comm['emails_processed']}
- WhatsApp messages: {comm['whatsapp_messages']}
- Pending responses: {comm['pending_responses']}"""

        return f"""---
type: ceo_briefing
week_start: {start}
week_end: {end}
generated_at: {generated_at}
data_sources: {sources_yaml}
missing_sources: {missing_yaml}
---

# Monday Morning CEO Briefing
## Week of {start_str} – {end_str}

{financial}

{social}

{communications}

## Action Items

_Review pending items in Needs_Action/ and Pending_Approval/ folders._

## Notes

{f'**Missing data sources**: {", ".join(missing_sources)}' if missing_sources else 'All data sources available.'}
"""

    def _email_briefing(self, filepath: Path) -> None:
        """Optionally email the CEO Briefing to the owner via fte-email MCP.

        Reads OWNER_EMAIL from .env. Skips silently if not configured.

        Args:
            filepath: Path to the generated briefing markdown file.
        """
        owner_email = os.getenv("OWNER_EMAIL", "")
        if not owner_email:
            logger.debug("OWNER_EMAIL not set — skipping briefing email")
            return

        try:
            from src.utils.email_sender import send_email
            content = filepath.read_text(encoding="utf-8")
            # Strip YAML frontmatter for email body
            if content.startswith("---"):
                end_idx = content.index("---", 3) + 3
                content = content[end_idx:].strip()

            send_email(
                to=owner_email,
                subject=f"CEO Briefing — {filepath.stem.replace('CEO_Briefing_', 'Week of ')}",
                body=content,
            )
            logger.info("CEO Briefing emailed to %s", owner_email)
        except Exception as e:
            logger.warning("Failed to email CEO Briefing: %s", e)
