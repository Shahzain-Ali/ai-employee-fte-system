"""Bulk delete company/automated emails from Gmail Primary inbox.

Usage:
    # Dry run — just count and preview (NO deletion)
    uv run scripts/bulk_delete_company_emails.py

    # Actually trash company emails
    uv run scripts/bulk_delete_company_emails.py --confirm

    # Trash emails matching a custom Gmail query
    uv run scripts/bulk_delete_company_emails.py --confirm --query "category:promotions"
"""
import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from googleapiclient.discovery import build
from src.watchers.gmail_auth import get_gmail_credentials
from src.watchers.gmail_watcher import _is_skip_sender
from email.utils import parseaddr

# ─── Gmail search queries that match company/automated emails ─────────────────
# These use Gmail's built-in categorization + common automated sender signals
COMPANY_EMAIL_QUERIES = [
    "in:inbox category:promotions",
    "in:inbox category:updates",
    "in:inbox category:forums",
    "in:inbox from:noreply",
    "in:inbox from:no-reply",
    "in:inbox from:donotreply",
    "in:inbox from:newsletter",
    "in:inbox from:notifications",
    "in:inbox from:marketing",
    "in:inbox unsubscribe",
]

BATCH_SIZE = 100  # Gmail API batchDelete supports up to 1000, keep it safe at 100


def get_messages_for_query(service, query: str) -> list[str]:
    """Return all message IDs matching the given Gmail query."""
    ids = []
    page_token = None
    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": 500}
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.users().messages().list(**kwargs).execute()
        messages = result.get("messages", [])
        ids.extend(m["id"] for m in messages)
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return ids


def get_message_sender(service, msg_id: str) -> tuple[str, str]:
    """Return (from_name, from_email) for a message ID."""
    try:
        msg = service.users().messages().get(
            userId="me", id=msg_id, format="metadata",
            metadataHeaders=["From", "Subject"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        from_raw = headers.get("From", "")
        subject = headers.get("Subject", "(no subject)")
        name, email = parseaddr(from_raw)
        return name, email.lower(), subject
    except Exception:
        return "", "", ""


def batch_trash(service, ids: list[str], dry_run: bool) -> int:
    """Trash messages in batches. Returns count trashed."""
    if dry_run:
        return len(ids)
    trashed = 0
    for i in range(0, len(ids), BATCH_SIZE):
        chunk = ids[i : i + BATCH_SIZE]
        service.users().messages().batchModify(
            userId="me",
            body={"ids": chunk, "removeLabelIds": ["INBOX"], "addLabelIds": ["TRASH"]},
        ).execute()
        trashed += len(chunk)
        print(f"  Trashed {trashed}/{len(ids)} ...", end="\r")
    print()
    return trashed


def main():
    parser = argparse.ArgumentParser(description="Bulk delete company emails from Gmail Primary")
    parser.add_argument(
        "--confirm", action="store_true",
        help="Actually trash the emails. Without this flag, only a dry-run is performed."
    )
    parser.add_argument(
        "--query", type=str, default=None,
        help="Custom Gmail search query (overrides default multi-query mode)"
    )
    parser.add_argument(
        "--preview", type=int, default=20,
        help="Number of sample emails to preview in dry-run (default: 20)"
    )
    args = parser.parse_args()

    dry_run = not args.confirm

    print("\n" + "=" * 60)
    print("  Gmail Company Email Bulk Deleter")
    print("=" * 60)
    if dry_run:
        print("  MODE: DRY RUN  (use --confirm to actually trash emails)")
    else:
        print("  MODE: LIVE — emails will be moved to Trash")
    print("=" * 60 + "\n")

    # Authenticate
    print("Authenticating with Gmail...")
    creds = get_gmail_credentials()
    service = build("gmail", "v1", credentials=creds)
    print("✓ Authenticated\n")

    # Collect all matching message IDs (dedup)
    queries = [args.query] if args.query else COMPANY_EMAIL_QUERIES
    all_ids: set[str] = set()

    for q in queries:
        print(f"Searching: {q}")
        ids = get_messages_for_query(service, q)
        print(f"  → {len(ids)} emails found")
        all_ids.update(ids)

    total = len(all_ids)
    print(f"\n{'─'*60}")
    print(f"Total unique company emails found: {total}")
    print(f"{'─'*60}\n")

    if total == 0:
        print("No company emails found. Nothing to do.")
        return

    # Preview sample emails
    sample_count = min(args.preview, total)
    print(f"Sample of {sample_count} emails to be trashed:\n")
    sample_ids = list(all_ids)[:sample_count]
    for i, msg_id in enumerate(sample_ids, 1):
        name, email, subject = get_message_sender(service, msg_id)
        is_company = _is_skip_sender(email) if email else True
        flag = "✓ company" if is_company else "? real person?"
        print(f"  {i:3}. [{flag}] From: {email or 'unknown'}")
        print(f"       Subject: {subject[:70]}")

    print(f"\n{'─'*60}")

    if dry_run:
        print(f"\nDRY RUN COMPLETE.")
        print(f"  {total} emails would be moved to Trash.")
        print(f"\nTo actually delete them, run:")
        print(f"  uv run scripts/bulk_delete_company_emails.py --confirm")
        print(f"\nNote: Trashed emails stay in Trash for 30 days before permanent deletion.")
        print(f"      You can restore them from Trash if needed.\n")
    else:
        print(f"\nAbout to move {total} emails to Trash.")
        answer = input("Type 'yes' to proceed, anything else to cancel: ").strip().lower()
        if answer != "yes":
            print("Cancelled. No emails were deleted.")
            return

        print(f"\nMoving {total} emails to Trash...")
        trashed = batch_trash(service, list(all_ids), dry_run=False)
        print(f"\n✓ Done! {trashed} emails moved to Trash.")
        print(f"  You can restore them from Gmail Trash within 30 days if needed.")


if __name__ == "__main__":
    main()
