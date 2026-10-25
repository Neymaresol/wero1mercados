"""Fail-closed read-only database guard BEFORE any startup DDL, seed or repair.

Both EXPECTED_DATABASE_NAME and EXPECTED_DATABASE_HOST must be explicitly
configured for each environment. A matching name/schema/host does not prove
physical instance identity, persistence, or a recoverable backup.
"""
import os
from urllib.parse import urlsplit, parse_qsl
from ops.p0_db_identity_preflight import QUERY, evaluate


def verify_prewrite_database(database_url, expected_name, expected_host, connect=None, required_host_suffix=None):
    """Raise a sanitized error on any ambiguity; never write or print secrets."""
    blocked = RuntimeError("P0 startup blocked: database preflight not verified")
    if not all(isinstance(v, str) and v.strip()
               for v in (database_url, expected_name, expected_host)):
        raise blocked
    try:
        parsed = urlsplit(database_url)
        params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        host = (parsed.hostname or "").lower().rstrip(".")
        expected = expected_host.strip().lower().rstrip(".")
        # libpq hostaddr/service can silently redirect a connection elsewhere.
        if (parsed.scheme not in ("postgres", "postgresql") or
                not host or "," in host or "," in expected or host != expected or
                any(k in params for k in ("host", "hostaddr", "service", "servicefile")) or
                os.getenv("PGHOSTADDR") or os.getenv("PGSERVICE") or
                (required_host_suffix and not host.endswith(required_host_suffix))):
            raise blocked
        if connect is None:
            import psycopg  # lazy: offline CI does not install DB drivers
            connector = psycopg.connect
        else:
            connector = connect
        with connector(database_url, connect_timeout=5,
                       options="-c default_transaction_read_only=on") as conn:
            with conn.cursor() as cur:
                cur.execute(QUERY)
                verdict = evaluate(cur.fetchone(), expected_name.strip())
                if verdict["status"] != "pass":
                    raise blocked
    except Exception:
        raise RuntimeError("P0 startup blocked: database preflight not verified") from None


def check_startup_database():
    # A staging service must never accept the Render production database host,
    # even if EXPECTED_DATABASE_HOST was copied from production by mistake.
    # This is an extra provider boundary, NOT physical-instance proof.
    mode = os.getenv("WERO_MODE", "homologation").strip().lower()
    if mode not in ("production", "homologation"):
        raise RuntimeError("P0 startup blocked: invalid deployment mode")
    verify_prewrite_database(
        os.getenv("DATABASE_URL", ""),
        os.getenv("EXPECTED_DATABASE_NAME", ""),
        os.getenv("EXPECTED_DATABASE_HOST", ""),
        required_host_suffix=".neon.tech" if mode == "homologation" else None,
    )
