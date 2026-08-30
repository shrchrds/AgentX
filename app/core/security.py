"""Security utilities for AgentX.

Provides API-key verification, FastAPI dependency for auth enforcement,
and input sanitization helpers.
"""

from __future__ import annotations

import re
import secrets

from fastapi import Header, HTTPException, status

from app.core.config import settings

# Maximum allowed length for user-supplied text inputs (e.g. task input_data)
MAX_INPUT_LENGTH = 50_000

# Control characters to strip (excluding newline, tab, carriage return)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def verify_api_key(api_key: str) -> bool:
    """Validate an API key against the configured secret.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        api_key: The key to validate.

    Returns:
        True if the key matches, False otherwise.
    """
    if not settings.api_secret_key:
        # If no secret key is configured, allow all requests (dev mode).
        return True
    return secrets.compare_digest(api_key, settings.api_secret_key)


async def get_api_key(
    x_api_key: str = Header(
        ...,
        alias="X-API-Key",
        description="API key for authentication",
    ),
) -> str:
    """FastAPI dependency that enforces API-key authentication.

    Raises:
        HTTPException: 401 if the key is missing or invalid.
    """
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key


def sanitize_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """Sanitize user-supplied text input.

    - Strips leading/trailing whitespace.
    - Removes control characters (preserving newlines and tabs).
    - Truncates to ``max_length``.

    Args:
        text: Raw user input.
        max_length: Maximum allowed character count.

    Returns:
        Sanitized string.
    """
    text = text.strip()
    text = _CONTROL_CHAR_RE.sub("", text)
    if len(text) > max_length:
        text = text[:max_length]
    return text
