"""Read-only, credential-free PostgreSQL connection identity diagnostics.

Do not return database URL, hostname, username, IP, or password.
This module is not mounted on any public endpoint.
"""
from hashlib import sha256
from urllib.parse import urlsplit
import os


def safe_connection_identity(database_url=None, environment=None):
    url = database_url if database_url is not None else os.getenv("DATABASE_URL", "")
    env = environment if environment is not None else os.getenv("WERO_MODE", "unknown")
    if not url:
        return {"configured": False, "environment": env, "identity": None}
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname:
            raise ValueError("invalid database URL")
        # Stable opaque fingerprint for cross-environment comparison only.
        # No credentials, username or URL in the digest input.
        canonical = f"{parsed.hostname.lower()}:{parsed.port or 5432}/{parsed.path.lstrip('/')}"
        digest = sha256(canonical.encode("utf-8")).hexdigest()[:16]
        return {"configured": True, "environment": env, "identity": digest}
    except (ValueError, TypeError):
        return {"configured": True, "environment": env, "identity": None, "error": "invalid_configuration"}


def verify_isolation(production, staging):
    """Fail closed when identities are absent, invalid or equal."""
    prod = production.get("identity")
    stage = staging.get("identity")
    return {"isolated": bool(prod and stage and prod != stage),
            "production_configured": bool(production.get("configured")),
            "staging_configured": bool(staging.get("configured"))}
