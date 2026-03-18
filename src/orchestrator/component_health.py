"""Component health registry — tracks status of all system components."""
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

HEALTH_FILE = ".state/health.json"

# Status thresholds
DEGRADED_THRESHOLD = 1  # consecutive failures to mark degraded
DOWN_THRESHOLD = 3      # consecutive failures to mark down


class ComponentHealthRegistry:
    """Tracks health status of system components (Odoo, Facebook, Instagram, Gmail, WhatsApp).

    Status values: healthy, degraded, down, unknown.
    State persisted to .state/health.json.
    """

    COMPONENTS = {
        "odoo": "Odoo (Docker)",
        "facebook": "Facebook Graph API",
        "instagram": "Instagram Graph API",
        "twitter": "Twitter/X (Playwright)",
        "linkedin": "LinkedIn (Playwright)",
        "gmail": "Gmail Watcher",
        "whatsapp": "WhatsApp Watcher",
    }

    def __init__(self, state_dir: Path | str = ".state"):
        self._state_dir = Path(state_dir)
        self._health_file = self._state_dir / "health.json"
        self._state = self._load_state()

    def _load_state(self) -> dict:
        """Load health state from disk, or initialize defaults."""
        if self._health_file.exists():
            try:
                return json.loads(self._health_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        # Initialize with unknown status
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {
            "components": {
                key: {
                    "name": name,
                    "status": "unknown",
                    "last_check": now,
                    "last_error": None,
                    "consecutive_failures": 0,
                }
                for key, name in self.COMPONENTS.items()
            },
            "updated_at": now,
        }

    def _save_state(self) -> None:
        """Persist health state to disk."""
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._state["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            self._health_file.write_text(
                json.dumps(self._state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            logger.error("Failed to save health state: %s", e)

    def update_health(self, domain: str, success: bool, error: str | None = None) -> str:
        """Update health status for a component based on operation result.

        Args:
            domain: Component key (odoo, facebook, instagram, gmail, whatsapp).
            success: Whether the operation succeeded.
            error: Error message if failed.

        Returns:
            New status string.
        """
        if domain not in self._state["components"]:
            logger.warning("Unknown domain: %s", domain)
            return "unknown"

        component = self._state["components"][domain]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        old_status = component["status"]

        component["last_check"] = now

        if success:
            component["status"] = "healthy"
            component["consecutive_failures"] = 0
            component["last_error"] = None
        else:
            component["consecutive_failures"] += 1
            component["last_error"] = error
            failures = component["consecutive_failures"]

            if failures >= DOWN_THRESHOLD:
                component["status"] = "down"
            elif failures >= DEGRADED_THRESHOLD:
                component["status"] = "degraded"

        self._save_state()

        new_status = component["status"]
        if old_status != new_status:
            logger.info(
                "Component %s health changed: %s → %s",
                domain, old_status, new_status,
            )
            # Create notification when component goes down
            if new_status == "down":
                self._create_down_notification(domain, component["name"], error)

        return new_status

    def _create_down_notification(self, domain: str, name: str, error: str | None) -> None:
        """Create notification file when a component transitions to down.

        Args:
            domain: Component key.
            name: Human-readable component name.
            error: Last error message.
        """
        # Find vault path (walk up from .state/)
        vault_path = self._state_dir.parent / "AI_Employee_Vault"
        if not vault_path.exists():
            # Try common location
            vault_path = Path("AI_Employee_Vault")
        needs_action = vault_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"NOTIFICATION_{domain}_down_{ts}.md"
        content = f"""---
type: notification
severity: critical
component: {domain}
created_at: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
---

# Component Down: {name}

**Component**: {domain}
**Status**: DOWN (3+ consecutive failures)
**Last Error**: {error or 'Unknown'}

## Suggested Action

1. Check if {name} is running and accessible
2. Review recent logs in `Logs/` for error details
3. Restart the component if needed
"""
        try:
            (needs_action / filename).write_text(content, encoding="utf-8")
            logger.warning("Created notification: %s", filename)
        except OSError as e:
            logger.error("Failed to create notification: %s", e)

    def get_health(self, domain: str) -> dict | None:
        """Get health status for a specific component.

        Args:
            domain: Component key.

        Returns:
            Component health dict or None if unknown domain.
        """
        return self._state["components"].get(domain)

    def get_all_health(self) -> dict:
        """Get health status for all components.

        Returns:
            Dict of all component health states.
        """
        return self._state["components"]
