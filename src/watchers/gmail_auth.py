"""Gmail OAuth2 authentication — handles credentials, tokens, and refresh."""
import os
import logging
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# Gmail API scopes — read for watcher, modify for marking read, send for replies
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


def get_gmail_credentials(
    credentials_path: str | None = None,
    token_path: str | None = None,
) -> Credentials:
    """Get valid Gmail API credentials with automatic token refresh.

    First-time: Opens browser for OAuth2 consent flow.
    Subsequent: Loads saved token, refreshes if expired.

    Args:
        credentials_path: Path to Google OAuth2 client credentials JSON.
        token_path: Path to store/load the OAuth2 token JSON.

    Returns:
        Valid Google OAuth2 Credentials object.

    Raises:
        FileNotFoundError: If credentials_path does not exist.
        ValueError: If credentials_path is not set.
    """
    credentials_path = credentials_path or os.getenv("GMAIL_CREDENTIALS_PATH")
    token_path = token_path or os.getenv("GMAIL_TOKEN_PATH")

    if not credentials_path:
        raise ValueError(
            "Gmail credentials path not set. "
            "Set GMAIL_CREDENTIALS_PATH in .env or pass credentials_path argument."
        )

    credentials_file = Path(credentials_path)
    if not credentials_file.exists():
        raise FileNotFoundError(
            f"Gmail credentials file not found: {credentials_file}\n"
            "Download it from Google Cloud Console → APIs & Services → Credentials."
        )

    token_file = Path(token_path) if token_path else Path(".secrets/gmail_token.json")

    creds = None

    # Load existing token
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            logger.debug("Loaded existing Gmail token from %s", token_file)
        except Exception as e:
            logger.warning("Failed to load token, will re-authorize: %s", e)
            creds = None

    # Refresh or authorize
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logger.info("Gmail token refreshed successfully")
            _save_token(creds, token_file)
        except Exception as e:
            logger.warning("Token refresh failed, will re-authorize: %s", e)
            creds = None

    if not creds or not creds.valid:
        logger.info("Starting Gmail OAuth2 authorization flow...")
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_file), SCOPES
        )
        creds = flow.run_local_server(port=0)
        logger.info("Gmail authorization successful")
        _save_token(creds, token_file)

    return creds


def _save_token(creds: Credentials, token_file: Path) -> None:
    """Save credentials token to file for reuse."""
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    logger.debug("Gmail token saved to %s", token_file)
