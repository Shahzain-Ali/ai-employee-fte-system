"""Health Monitor — checks Cloud VM components and auto-restarts on failure."""
import json
import logging
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Thresholds
DISK_WARNING_PERCENT = 85
RAM_WARNING_PERCENT = 90
MAX_RESTART_ATTEMPTS = 3


class HealthCheckResult:
    """Result of a health check run."""

    def __init__(self):
        self.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.overall = "healthy"
        self.components: dict[str, dict] = {}
        self.alerts: list[str] = []

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "overall": self.overall,
            "components": self.components,
            "alerts": self.alerts,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class HealthMonitor:
    """Monitors all Cloud VM components and auto-restarts on failure."""

    def __init__(self, vault_path: Path, log_dir: Path | None = None):
        self.vault_path = Path(vault_path)
        self.log_dir = Path(log_dir or "/var/log/fte-health")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._restart_counts: dict[str, int] = {}

    def run_all_checks(self) -> HealthCheckResult:
        """Run all health checks and return results."""
        result = HealthCheckResult()

        result.components["odoo"] = self.check_odoo()
        result.components["email_watcher"] = self.check_process("gmail_watcher", "email-watcher")
        result.components["orchestrator"] = self.check_process("cloud_orchestrator", "cloud-orchestrator")
        result.components["git_sync"] = self.check_git_sync()
        result.components["disk"] = self.check_disk()
        result.components["ram"] = self.check_ram()

        # Determine overall status
        statuses = [c.get("status", "unknown") for c in result.components.values()]
        if "down" in statuses:
            result.overall = "degraded"
            result.alerts.extend(
                f"{name} is DOWN" for name, c in result.components.items()
                if c.get("status") == "down"
            )
        if all(s == "down" for s in statuses):
            result.overall = "critical"

        # Save result to log
        self._save_result(result)

        # Auto-restart failed components
        for name, component in result.components.items():
            if component.get("status") == "down" and component.get("pm2_name"):
                self._auto_restart(name, component["pm2_name"], result)

        return result

    def check_odoo(self) -> dict:
        """Check if Odoo is responding on localhost:8069."""
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "--connect-timeout", "5", "http://localhost:8069"],
                capture_output=True, text=True, timeout=10,
            )
            status_code = result.stdout.strip()
            is_up = status_code in ("200", "301", "302", "303")
            return {
                "status": "up" if is_up else "down",
                "http_status": status_code,
                "pm2_name": None,  # Odoo runs in Docker, not PM2
            }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"status": "down", "error": "timeout or curl not found", "pm2_name": None}

    def check_process(self, grep_name: str, pm2_name: str) -> dict:
        """Check if a process is running via pgrep.

        Args:
            grep_name: Process name to search for with pgrep.
            pm2_name: PM2 process name for auto-restart.
        """
        try:
            result = subprocess.run(
                ["pgrep", "-f", grep_name],
                capture_output=True, text=True, timeout=5,
            )
            pids = result.stdout.strip().splitlines()
            is_up = len(pids) > 0
            return {
                "status": "up" if is_up else "down",
                "pid": int(pids[0]) if pids else None,
                "pm2_name": pm2_name,
            }
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            return {"status": "unknown", "pm2_name": pm2_name}

    def check_git_sync(self) -> dict:
        """Check git sync health by looking at last push timestamp."""
        refs_path = self.vault_path / ".git" / "refs" / "remotes" / "origin" / "main"
        try:
            if refs_path.exists():
                mtime = refs_path.stat().st_mtime
                age_seconds = time.time() - mtime
                is_recent = age_seconds < 600  # Less than 10 minutes
                return {
                    "status": "up" if is_recent else "warning",
                    "last_sync_age_seconds": int(age_seconds),
                    "pm2_name": "gitwatch",
                }
            return {"status": "unknown", "error": "no remote ref found", "pm2_name": "gitwatch"}
        except OSError:
            return {"status": "unknown", "pm2_name": "gitwatch"}

    def check_disk(self) -> dict:
        """Check disk usage."""
        try:
            usage = shutil.disk_usage("/")
            percent = (usage.used / usage.total) * 100
            status = "ok" if percent < DISK_WARNING_PERCENT else "warning"
            return {
                "status": status,
                "usage_percent": round(percent, 1),
                "free_gb": round(usage.free / (1024**3), 1),
            }
        except OSError:
            return {"status": "unknown"}

    def check_ram(self) -> dict:
        """Check RAM usage via /proc/meminfo."""
        try:
            meminfo = Path("/proc/meminfo").read_text()
            values = {}
            for line in meminfo.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    values[key] = int(parts[1])

            total = values.get("MemTotal", 1)
            available = values.get("MemAvailable", 0)
            used_percent = ((total - available) / total) * 100

            status = "ok" if used_percent < RAM_WARNING_PERCENT else "warning"
            return {
                "status": status,
                "usage_percent": round(used_percent, 1),
                "available_mb": round(available / 1024, 0),
            }
        except (OSError, ValueError, ZeroDivisionError):
            return {"status": "unknown"}

    def _auto_restart(self, component_name: str, pm2_name: str, result: HealthCheckResult) -> None:
        """Attempt to auto-restart a failed component via PM2.

        Args:
            component_name: Human name of the component.
            pm2_name: PM2 process name.
            result: Current health check result (for adding alerts).
        """
        count = self._restart_counts.get(component_name, 0)

        if count >= MAX_RESTART_ATTEMPTS:
            alert_msg = f"{component_name}: {MAX_RESTART_ATTEMPTS} restart attempts failed"
            result.alerts.append(alert_msg)
            logger.error(alert_msg)
            self._create_alert_file(component_name, alert_msg)
            return

        logger.info("Auto-restarting %s (attempt %d/%d)", pm2_name, count + 1, MAX_RESTART_ATTEMPTS)

        try:
            subprocess.run(
                ["pm2", "restart", pm2_name],
                capture_output=True, text=True, timeout=30,
            )
            self._restart_counts[component_name] = count + 1
            logger.info("Restart issued for %s", pm2_name)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error("Failed to restart %s: %s", pm2_name, e)

    def _create_alert_file(self, component: str, message: str) -> None:
        """Create alert file in vault Updates/ (syncs to Local via git)."""
        updates_dir = self.vault_path / "Updates"
        updates_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"alert_{component}_{ts}.md"
        filepath = updates_dir / filename

        content = f"""---
agent: cloud
timestamp: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
type: alert
severity: critical
component: {component}
---

# ⚠️ Alert: {component} Failed

{message}

Auto-restart attempts exhausted. Manual intervention required.
"""
        filepath.write_text(content, encoding="utf-8")
        logger.warning("Alert file created: %s", filename)

    def _save_result(self, result: HealthCheckResult) -> None:
        """Save health check result to log file."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filepath = self.log_dir / f"health_{ts}.json"
        try:
            filepath.write_text(result.to_json(), encoding="utf-8")
        except OSError as e:
            logger.error("Failed to save health result: %s", e)


def main():
    """Entry point for health monitor."""
    import os
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [health] %(levelname)s: %(message)s",
    )

    vault_path = Path(os.getenv("VAULT_PATH", "/home/ubuntu/vault"))
    monitor = HealthMonitor(vault_path=vault_path)
    result = monitor.run_all_checks()

    print(result.to_json())
    if result.overall != "healthy":
        logger.warning("Overall health: %s", result.overall)


if __name__ == "__main__":
    main()
