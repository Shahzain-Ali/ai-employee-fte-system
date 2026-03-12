"""Retry utility — exponential backoff for transient errors."""
import time
import logging
import functools
from typing import Callable

logger = logging.getLogger(__name__)

# Action types that must NEVER be retried (financial/payment operations)
NO_RETRY_ACTIONS = frozenset({
    "mark_payment_received",
    "odoo_payment",
    "payment",
    "create_expense",
})


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError, OSError),
):
    """Decorator that retries a function with exponential backoff.

    Delays: base_delay * 2^attempt (1s, 2s, 4s for default settings).
    Never retries payment/financial actions.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds before first retry.
        retryable_exceptions: Tuple of exception types to retry on.

    Returns:
        Decorated function with retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if this is a financial action that should not be retried
            action_type = kwargs.get("action_type", "")
            if action_type in NO_RETRY_ACTIONS:
                return func(*args, **kwargs)

            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            "Retry %d/%d for %s after error: %s (delay: %.1fs)",
                            attempt + 1, max_retries, func.__name__, e, delay,
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "All %d retries exhausted for %s: %s",
                            max_retries, func.__name__, e,
                        )
            raise last_exception

        return wrapper
    return decorator


def is_rate_limited(headers: dict) -> bool:
    """Check Meta Graph API X-App-Usage header for rate limiting.

    Args:
        headers: Response headers dict.

    Returns:
        True if approaching or at rate limit.
    """
    usage = headers.get("X-App-Usage") or headers.get("x-app-usage")
    if not usage:
        return False

    import json
    try:
        data = json.loads(usage) if isinstance(usage, str) else usage
        # Meta considers >80% as approaching limit
        call_count = data.get("call_count", 0)
        total_cputime = data.get("total_cputime", 0)
        total_time = data.get("total_time", 0)
        return max(call_count, total_cputime, total_time) > 80
    except (json.JSONDecodeError, TypeError):
        return False
