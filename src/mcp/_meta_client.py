"""Shared Meta Graph API client for Facebook and Instagram MCP servers."""
import sys
import json
import logging
from typing import Any

import requests

from src.utils.retry import retry_with_backoff, is_rate_limited

logger = logging.getLogger(__name__)


class MetaGraphClient:
    """HTTP client for Meta Graph API with retry, rate limit, and token handling.

    Used by both fte-facebook and fte-instagram MCP servers.

    Args:
        access_token: Page Access Token for the Meta API.
        api_version: API version string (e.g., 'v21.0').
    """

    BASE_URL = "https://graph.facebook.com"

    def __init__(self, access_token: str, api_version: str = "v21.0"):
        self.access_token = access_token
        self.api_version = api_version
        self._base = f"{self.BASE_URL}/{self.api_version}"

    @retry_with_backoff(max_retries=3, base_delay=1.0,
                        retryable_exceptions=(ConnectionError, TimeoutError, OSError))
    def get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request to the Meta Graph API.

        Args:
            endpoint: API endpoint path (e.g., '/{page-id}/feed').
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            ConnectionError: If the API is unreachable.
            RuntimeError: If the API returns an error.
        """
        url = f"{self._base}{endpoint}"
        p = dict(params or {})
        p["access_token"] = self.access_token

        logger.info("GET %s", endpoint)
        try:
            resp = requests.get(url, params=p, timeout=30)
        except requests.ConnectionError:
            raise ConnectionError(f"Cannot reach Meta Graph API at {url}")
        except requests.Timeout:
            raise TimeoutError(f"Meta Graph API request timed out: {url}")

        return self._handle_response(resp)

    @retry_with_backoff(max_retries=3, base_delay=1.0,
                        retryable_exceptions=(ConnectionError, TimeoutError, OSError))
    def post(self, endpoint: str, data: dict | None = None) -> dict:
        """Make a POST request to the Meta Graph API.

        Args:
            endpoint: API endpoint path.
            data: Request body data.

        Returns:
            Parsed JSON response.

        Raises:
            ConnectionError: If the API is unreachable.
            RuntimeError: If the API returns an error.
        """
        url = f"{self._base}{endpoint}"
        d = dict(data or {})
        d["access_token"] = self.access_token

        logger.info("POST %s", endpoint)
        try:
            resp = requests.post(url, data=d, timeout=30)
        except requests.ConnectionError:
            raise ConnectionError(f"Cannot reach Meta Graph API at {url}")
        except requests.Timeout:
            raise TimeoutError(f"Meta Graph API request timed out: {url}")

        return self._handle_response(resp)

    def _handle_response(self, resp: requests.Response) -> dict:
        """Parse and validate API response.

        Args:
            resp: The HTTP response object.

        Returns:
            Parsed JSON data.

        Raises:
            RuntimeError: If the API returned an error.
        """
        # Check rate limiting
        if is_rate_limited(dict(resp.headers)):
            logger.warning("Approaching Meta API rate limit")

        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(f"Invalid JSON response from Meta API (status {resp.status_code})")

        if "error" in data:
            err = data["error"]
            code = err.get("code", "")
            msg = err.get("message", str(err))
            err_type = err.get("type", "")

            # Token expiration
            if code == 190:
                raise RuntimeError(
                    f"Meta API token expired or invalid (OAuthException code 190): {msg}. "
                    "Regenerate your Page Access Token."
                )

            # Permission error
            if code in (10, 200):
                raise RuntimeError(f"Meta API permission denied ({err_type}): {msg}")

            raise RuntimeError(f"Meta API error ({code} {err_type}): {msg}")

        return data
