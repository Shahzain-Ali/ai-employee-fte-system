"""Git Sync — manages vault synchronization between Cloud and Local via GitHub."""
import logging
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Sensitive file patterns that must NEVER be committed
SENSITIVE_PATTERNS = [
    ".env", "*.token", "*.session", "*credentials*",
    "*.key", "*.pem", "whatsapp-session/", "banking/",
    "*secret*", "*.pickle", "*.p12",
]


def git_push(vault_path: Path, agent: str = "cloud") -> bool:
    """Stage all changes and push to GitHub with auto-commit message.

    Args:
        vault_path: Path to the vault git repository.
        agent: Agent identifier for commit message.

    Returns:
        True if push succeeded, False otherwise.
    """
    vault = Path(vault_path)

    # Validate no sensitive files before staging
    if not validate_vault_security(vault):
        logger.error("Security check failed — aborting push")
        return False

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    commit_msg = f"auto: {agent} {ts}"

    try:
        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(vault), capture_output=True, text=True, check=True,
        )

        # Check if there's anything to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(vault), capture_output=True, text=True, check=True,
        )
        if not status.stdout.strip():
            logger.debug("Nothing to commit")
            return True

        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(vault), capture_output=True, text=True, check=True,
        )

        # Push
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(vault), capture_output=True, text=True, timeout=60,
        )

        if result.returncode == 0:
            logger.info("Git push succeeded: %s", commit_msg)
            return True
        else:
            logger.error("Git push failed: %s", result.stderr[:500])
            return False

    except subprocess.CalledProcessError as e:
        logger.error("Git command failed: %s", e.stderr[:500] if e.stderr else str(e))
        return False
    except subprocess.TimeoutExpired:
        logger.error("Git push timed out")
        return False


def git_pull_rebase(vault_path: Path) -> bool:
    """Pull latest changes from GitHub with rebase and conflict resolution.

    Conflict resolution per protocol:
    - Task files: accept theirs (remote wins — claim-by-move)
    - Dashboard.md: accept ours (local wins — single-writer)
    - Log files: concatenate (append-only)
    - Updates/: accept theirs (unique timestamp filenames)

    Args:
        vault_path: Path to the vault git repository.

    Returns:
        True if pull succeeded, False otherwise.
    """
    vault = Path(vault_path)

    try:
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=str(vault), capture_output=True, text=True, timeout=60,
        )

        if result.returncode == 0:
            logger.debug("Git pull succeeded")
            return True

        # Handle conflicts
        if "CONFLICT" in result.stdout or "CONFLICT" in result.stderr:
            logger.warning("Merge conflicts detected — attempting resolution")
            return _resolve_conflicts(vault)

        logger.error("Git pull failed: %s", result.stderr[:500])
        return False

    except subprocess.CalledProcessError as e:
        logger.error("Git pull error: %s", e.stderr[:500] if e.stderr else str(e))
        return False
    except subprocess.TimeoutExpired:
        logger.error("Git pull timed out")
        return False


def _resolve_conflicts(vault_path: Path) -> bool:
    """Resolve merge conflicts per the Cloud-Local protocol.

    Args:
        vault_path: Path to the vault git repository.

    Returns:
        True if all conflicts resolved, False otherwise.
    """
    # Get list of conflicted files
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=U"],
        cwd=str(vault_path), capture_output=True, text=True,
    )

    if not result.stdout.strip():
        return True

    conflicted = result.stdout.strip().splitlines()
    all_resolved = True

    for filepath in conflicted:
        resolved = _resolve_single_conflict(vault_path, filepath)
        if resolved:
            subprocess.run(
                ["git", "add", filepath],
                cwd=str(vault_path), capture_output=True, text=True,
            )
        else:
            all_resolved = False
            logger.error("Could not auto-resolve conflict: %s", filepath)

    if all_resolved:
        subprocess.run(
            ["git", "rebase", "--continue"],
            cwd=str(vault_path), capture_output=True, text=True,
            env={"GIT_EDITOR": "true", **__import__("os").environ},
        )
        logger.info("All conflicts resolved successfully")
        return True

    # Abort rebase on unresolvable conflicts
    subprocess.run(
        ["git", "rebase", "--abort"],
        cwd=str(vault_path), capture_output=True, text=True,
    )
    logger.error("Unresolvable conflicts — rebase aborted")
    return False


def _resolve_single_conflict(vault_path: Path, filepath: str) -> bool:
    """Resolve a single file conflict based on its location.

    Args:
        vault_path: Path to the vault git repository.
        filepath: Relative path of the conflicted file.

    Returns:
        True if resolved, False if needs manual intervention.
    """
    # Dashboard.md → accept ours (local is single-writer)
    if filepath == "Dashboard.md":
        subprocess.run(
            ["git", "checkout", "--ours", filepath],
            cwd=str(vault_path), capture_output=True, text=True,
        )
        logger.info("Resolved %s: accept ours (single-writer)", filepath)
        return True

    # Task files in Needs_Action/ or In_Progress/ → accept theirs
    if filepath.startswith(("Needs_Action/", "In_Progress/", "Updates/")):
        subprocess.run(
            ["git", "checkout", "--theirs", filepath],
            cwd=str(vault_path), capture_output=True, text=True,
        )
        logger.info("Resolved %s: accept theirs (claim-by-move)", filepath)
        return True

    # Log files → concatenate both versions
    if filepath.startswith("Logs/"):
        return _concat_resolve(vault_path, filepath)

    # Default: accept theirs
    subprocess.run(
        ["git", "checkout", "--theirs", filepath],
        cwd=str(vault_path), capture_output=True, text=True,
    )
    logger.info("Resolved %s: accept theirs (default)", filepath)
    return True


def _concat_resolve(vault_path: Path, filepath: str) -> bool:
    """Resolve a log file conflict by concatenating both versions.

    Args:
        vault_path: Path to the vault git repository.
        filepath: Relative path of the conflicted log file.

    Returns:
        True if resolved.
    """
    full_path = vault_path / filepath
    try:
        content = full_path.read_text(encoding="utf-8")
        # Remove git conflict markers and keep both sides
        cleaned = re.sub(r"<<<<<<<.*?\n", "", content)
        cleaned = re.sub(r"=======\n", "", cleaned)
        cleaned = re.sub(r">>>>>>>.*?\n", "", cleaned)
        full_path.write_text(cleaned, encoding="utf-8")
        logger.info("Resolved %s: concatenated both versions", filepath)
        return True
    except OSError as e:
        logger.error("Failed to concat-resolve %s: %s", filepath, e)
        return False


def check_sync_status(vault_path: Path) -> dict:
    """Check the current sync status of the vault.

    Returns:
        Dict with 'last_push', 'last_pull', 'is_clean', 'behind', 'ahead'.
    """
    vault = Path(vault_path)
    status = {
        "last_push": None,
        "last_pull": None,
        "is_clean": True,
        "behind": 0,
        "ahead": 0,
    }

    try:
        # Check if working tree is clean
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(vault), capture_output=True, text=True,
        )
        status["is_clean"] = not bool(result.stdout.strip())

        # Check ahead/behind
        result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", "HEAD...origin/main"],
            cwd=str(vault), capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split()
            if len(parts) == 2:
                status["ahead"] = int(parts[0])
                status["behind"] = int(parts[1])

        # Last push timestamp (from reflog)
        refs_path = vault / ".git" / "refs" / "remotes" / "origin" / "main"
        if refs_path.exists():
            mtime = refs_path.stat().st_mtime
            status["last_push"] = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

    except (subprocess.CalledProcessError, OSError, ValueError) as e:
        logger.error("Failed to check sync status: %s", e)

    return status


def is_github_reachable() -> bool:
    """Check if GitHub is reachable via SSH.

    Returns:
        True if SSH connection to github.com succeeds.
    """
    try:
        result = subprocess.run(
            ["ssh", "-T", "-o", "ConnectTimeout=5", "git@github.com"],
            capture_output=True, text=True, timeout=10,
        )
        # GitHub returns exit code 1 but prints "successfully authenticated"
        return "successfully authenticated" in result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def validate_vault_security(vault_path: Path) -> bool:
    """Validate that no sensitive files are in the git staging area.

    Scans staged files against sensitive patterns before allowing push.

    Args:
        vault_path: Path to the vault git repository.

    Returns:
        True if safe to push, False if sensitive files detected.
    """
    vault = Path(vault_path)

    try:
        # Get list of staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(vault), capture_output=True, text=True,
        )
        staged_files = result.stdout.strip().splitlines() if result.stdout.strip() else []

        # Also check untracked files that might get added
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(vault), capture_output=True, text=True,
        )
        untracked = result.stdout.strip().splitlines() if result.stdout.strip() else []

        all_files = staged_files + untracked

        for filepath in all_files:
            filename = Path(filepath).name
            for pattern in SENSITIVE_PATTERNS:
                if pattern.startswith("*") and pattern.endswith("*"):
                    # Contains pattern: *secret* matches anything with "secret"
                    keyword = pattern.strip("*")
                    if keyword in filename.lower():
                        logger.error("SECURITY: Blocked sensitive file: %s (matches %s)", filepath, pattern)
                        return False
                elif pattern.startswith("*."):
                    # Extension pattern: *.key, *.pem
                    ext = pattern[1:]  # .key, .pem
                    if filename.endswith(ext):
                        logger.error("SECURITY: Blocked sensitive file: %s (matches %s)", filepath, pattern)
                        return False
                elif pattern.endswith("/"):
                    # Directory pattern: whatsapp-session/
                    if filepath.startswith(pattern) or f"/{pattern}" in filepath:
                        logger.error("SECURITY: Blocked sensitive file: %s (matches %s)", filepath, pattern)
                        return False
                else:
                    # Exact match: .env
                    if filename == pattern:
                        logger.error("SECURITY: Blocked sensitive file: %s (matches %s)", filepath, pattern)
                        return False

        return True

    except subprocess.CalledProcessError as e:
        logger.error("Security validation failed: %s", e)
        return False
