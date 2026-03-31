"""Personal AI Employee — Gold Tier Autonomous Employee entry point."""
import sys
import os
import logging
import threading
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "help"

    if command == "setup":
        _run_setup()
    elif command == "run":
        _run_system()
    elif command == "gmail":
        _run_gmail()
    elif command == "whatsapp":
        _run_whatsapp()
    elif command == "briefing":
        _run_briefing()
    elif command == "dashboard":
        _run_dashboard()
    elif command == "help":
        _print_help()
    else:
        print(f"Unknown command: {command}")
        _print_help()
        sys.exit(1)


def _run_setup():
    """Initialize the vault and create core files."""
    from src.utils.vault_init import create_vault, create_vault_files

    vault_path_str = os.getenv("VAULT_PATH", "AI_Employee_Vault")
    vault_path = Path(vault_path_str)

    print(f"Setting up vault at: {vault_path.resolve()}")
    create_vault(vault_path)
    create_vault_files(vault_path)

    # Silver tier directories
    (vault_path / "Plans").mkdir(exist_ok=True)

    # Gold tier directories
    (vault_path / "Briefings").mkdir(exist_ok=True)
    (vault_path / "Tasks").mkdir(exist_ok=True)
    Path(".state").mkdir(exist_ok=True)

    print("Vault setup complete.")
    print(f"  Folders: Inbox, Needs_Action, Done, Logs, Pending_Approval, Approved, Rejected, Plans, Briefings, Tasks")
    print(f"  Files: Dashboard.md, Company_Handbook.md")
    print(f"\nOpen the vault in Obsidian: {vault_path.resolve()}")


def _run_system():
    """Start watchers and orchestrator."""
    agent_mode = os.getenv("AGENT_MODE", "local")

    # Cloud mode — draft-only orchestrator, no watchers/approval needed
    if agent_mode == "cloud":
        _run_cloud_system()
        return

    from src.watchers.filesystem_watcher import FilesystemWatcher
    from src.orchestrator.orchestrator import Orchestrator
    from src.orchestrator.approval_watcher import ApprovalWatcher
    from src.orchestrator.approval_handler import ApprovalHandler

    vault_path_str = os.getenv("VAULT_PATH", "AI_Employee_Vault")
    vault_path = Path(vault_path_str)

    if not vault_path.exists():
        print(f"Vault not found at {vault_path}. Run 'python -m src.main setup' first.")
        sys.exit(1)

    poll_interval = int(os.getenv("POLL_INTERVAL", "60"))
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    print(f"Starting AI Employee system (LOCAL mode)...")
    print(f"  Vault: {vault_path.resolve()}")
    print(f"  Poll interval: {poll_interval}s")
    print(f"  Dry run: {dry_run}")

    # Start filesystem watcher
    watcher = FilesystemWatcher(vault_path=vault_path)
    watcher.start()

    # Start Gmail watcher in background thread (if credentials exist)
    gmail_creds = os.getenv("GMAIL_CREDENTIALS_PATH")
    if gmail_creds and Path(gmail_creds).exists():
        from src.watchers.gmail_watcher import GmailWatcher

        gmail = GmailWatcher(vault_path=vault_path)
        gmail_thread = threading.Thread(target=gmail.start, daemon=True, name="gmail-watcher")
        gmail_thread.start()
        print("  Gmail Watcher: STARTED")
    else:
        print("  Gmail Watcher: SKIPPED (no credentials)")

    # Start approval watcher with handler
    handler = ApprovalHandler(vault_path=vault_path)

    # Start WhatsApp watcher in background thread (if session exists)
    whatsapp_session = os.getenv("WHATSAPP_SESSION_PATH", ".sessions/whatsapp")
    if Path(whatsapp_session).exists():
        from src.watchers.whatsapp_watcher import WhatsAppWatcher

        wa = WhatsAppWatcher(vault_path=vault_path)
        wa_thread = threading.Thread(target=wa.start, daemon=True, name="whatsapp-watcher")
        wa_thread.start()
        # Link watcher to approval handler so it can reuse the browser for replies
        handler._whatsapp_watcher = wa
        print("  WhatsApp Watcher: STARTED")
    else:
        print("  WhatsApp Watcher: SKIPPED (run 'whatsapp --setup' first)")

    approval_watcher = ApprovalWatcher(vault_path=vault_path)
    approval_watcher.on_approved = handler.handle_approved
    approval_watcher.on_rejected = handler.handle_rejected
    approval_watcher.start()
    print("  Approval Watcher: STARTED")

    print()

    # Start orchestrator (blocking)
    orchestrator = Orchestrator(vault_path=vault_path, dry_run=dry_run)
    orchestrator.run()


def _run_cloud_system():
    """Start Cloud Agent — draft-only mode, no WhatsApp/approval watchers."""
    from src.orchestrator.cloud_orchestrator import CloudOrchestrator

    vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
    config_path = Path(os.getenv("CLOUD_CONFIG_PATH", "config/cloud-agent.yaml"))

    if not vault_path.exists():
        print(f"Vault not found at {vault_path}. Run 'python -m src.main setup' first.")
        sys.exit(1)

    print(f"Starting AI Employee system (CLOUD mode — draft only)...")
    print(f"  Vault: {vault_path.resolve()}")
    print(f"  Config: {config_path}")
    print(f"  Poll interval: {os.getenv('POLL_INTERVAL', '60')}s")

    # Start Gmail watcher in background thread (if credentials exist)
    gmail_creds = os.getenv("GMAIL_CREDENTIALS_PATH")
    if gmail_creds and Path(gmail_creds).exists():
        from src.watchers.gmail_watcher import GmailWatcher

        gmail = GmailWatcher(vault_path=vault_path)
        gmail_thread = threading.Thread(target=gmail.start, daemon=True, name="gmail-watcher")
        gmail_thread.start()
        print("  Gmail Watcher: STARTED")
    else:
        print("  Gmail Watcher: SKIPPED (no credentials)")

    print()

    # Start cloud orchestrator (blocking) — draft-only, no send/publish
    orchestrator = CloudOrchestrator(config_path=config_path, vault_path=vault_path)
    orchestrator.run()


def _run_gmail():
    """Run Gmail watcher standalone (for testing)."""
    flag = sys.argv[2] if len(sys.argv) > 2 else "--once"

    if flag == "--authorize":
        from src.watchers.gmail_watcher import _run_authorize
        _run_authorize()
    elif flag == "--once":
        from src.watchers.gmail_watcher import _run_once
        _run_once()
    else:
        vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
        from src.watchers.gmail_watcher import GmailWatcher
        watcher = GmailWatcher(vault_path=vault_path)
        try:
            watcher.start()
        except KeyboardInterrupt:
            watcher.stop()


def _run_whatsapp():
    """Run WhatsApp watcher standalone (for setup/testing)."""
    flag = sys.argv[2] if len(sys.argv) > 2 else "--once"

    if flag == "--setup":
        from src.watchers.whatsapp_watcher import _run_setup
        _run_setup()
    elif flag == "--once":
        from src.watchers.whatsapp_watcher import _run_once
        _run_once()
    else:
        vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
        from src.watchers.whatsapp_watcher import WhatsAppWatcher
        watcher = WhatsAppWatcher(vault_path=vault_path)
        try:
            watcher.start()
        except KeyboardInterrupt:
            watcher.stop()


def _run_briefing():
    """Manually trigger CEO Briefing generation."""
    vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))

    print("Generating CEO Briefing...")
    from src.utils.ceo_briefing import CEOBriefingGenerator
    generator = CEOBriefingGenerator(vault_path=vault_path)

    week_start = sys.argv[2] if len(sys.argv) > 2 else ""
    path = generator.generate(week_start=week_start)
    print(f"CEO Briefing generated: {path}")


def _run_dashboard():
    """Start the Streamlit dashboard."""
    import subprocess
    dashboard_path = Path(__file__).resolve().parent / "dashboard" / "app.py"
    print(f"Starting Dashboard at: {dashboard_path}")
    subprocess.run(["streamlit", "run", str(dashboard_path)])


def _print_help():
    print("Personal AI Employee — Gold Tier Autonomous Employee")
    print()
    print("Commands:")
    print("  setup                Initialize vault structure and core files")
    print("  run                  Start all watchers and orchestrator")
    print("  gmail --authorize    First-time Gmail OAuth2 setup")
    print("  gmail --once         Run one Gmail check and exit")
    print("  gmail --start        Run Gmail watcher continuously")
    print("  whatsapp --setup     First-time WhatsApp QR code scan")
    print("  whatsapp --once      Run one WhatsApp check and exit")
    print("  whatsapp --start     Run WhatsApp watcher continuously")
    print("  briefing             Manually trigger CEO Briefing")
    print("  briefing YYYY-MM-DD  Generate briefing for specific week start")
    print("  dashboard            Start Streamlit dashboard")
    print("  help                 Show this help message")
    print()
    print("Usage:")
    print("  python -m src.main setup")
    print("  python -m src.main gmail --authorize")
    print("  python -m src.main gmail --once")
    print("  python -m src.main whatsapp --setup")
    print("  python -m src.main whatsapp --once")
    print("  python -m src.main briefing")
    print("  python -m src.main dashboard")
    print("  python -m src.main run")


if __name__ == "__main__":
    main()
