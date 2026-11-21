"""Short-lived, single-use form token helpers for the outbound click boundary.

These tokens mitigate cross-site form submission and replay. They do not prove
that a browser user is human or that a partner-authenticated INT event occurred.
"""
from hashlib import sha256
from urllib.parse import parse_qs

MAX_BODY_BYTES = 2048
MIN_TOKEN_LENGTH = 32
MAX_TOKEN_LENGTH = 128


def _valid_token(token):
    return (
        isinstance(token, str)
        and MIN_TOKEN_LENGTH <= len(token) <= MAX_TOKEN_LENGTH
        and token.isascii()
        and all(char.isalnum() or char in "-_" for char in token)
    )


def extract_action_token(content_type, body):
    """Parse exactly one bounded token from a URL-encoded HTML form body."""
    media_type = (content_type or "").split(";", 1)[0].strip().lower()
    if media_type != "application/x-www-form-urlencoded":
        raise ValueError("unsupported form content type")
    if not isinstance(body, (bytes, bytearray)) or len(body) > MAX_BODY_BYTES:
        raise ValueError("invalid or oversized form body")
    try:
        fields = parse_qs(
            bytes(body).decode("utf-8"),
            strict_parsing=True,
            max_num_fields=8,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("malformed form body") from exc
    values = fields.get("action_token", [])
    if len(values) != 1 or not _valid_token(values[0]):
        raise ValueError("exactly one valid action token is required")
    return values[0]


def digest_action_token(token):
    """Return only a SHA-256 digest suitable for storage, never the raw token."""
    if not _valid_token(token):
        raise ValueError("invalid action token")
    return sha256(token.encode("utf-8")).hexdigest()
