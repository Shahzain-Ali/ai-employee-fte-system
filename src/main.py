"""Personal AI Employee — Bronze Tier entry point."""
import sys
import os
import logging
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
    print("Vault setup complete.")
    print(f"  Folders: Inbox, Needs_Action, Done, Logs, Pending_Approval, Approved, Rejected")
    print(f"  Files: Dashboard.md, Company_Handbook.md")
    print(f"\nOpen the vault in Obsidian: {vault_path.resolve()}")


def _run_system():
    """Start the file system watcher and orchestrator."""
    from src.watchers.filesystem_watcher import FilesystemWatcher
    from src.orchestrator.orchestrator import Orchestrator

    vault_path_str = os.getenv("VAULT_PATH", "AI_Employee_Vault")
    vault_path = Path(vault_path_str)

    if not vault_path.exists():
        print(f"Vault not found at {vault_path}. Run 'python -m src.main setup' first.")
        sys.exit(1)

    poll_interval = int(os.getenv("POLL_INTERVAL", "60"))
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    print(f"Starting AI Employee system...")
    print(f"  Vault: {vault_path.resolve()}")
    print(f"  Poll interval: {poll_interval}s")
    print(f"  Dry run: {dry_run}")
    print()

    watcher = FilesystemWatcher(vault_path=vault_path)
    orchestrator = Orchestrator(vault_path=vault_path, dry_run=dry_run)

    watcher.start()
    orchestrator.run()


def _print_help():
    print("Personal AI Employee — Bronze Tier")
    print()
    print("Commands:")
    print("  setup    Initialize vault structure and core files")
    print("  run      Start the file watcher and orchestrator")
    print("  help     Show this help message")
    print()
    print("Usage:")
    print("  python -m src.main setup")
    print("  python -m src.main run")


if __name__ == "__main__":
    main()
