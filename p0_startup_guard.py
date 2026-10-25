"""Fail-closed read-only database guard BEFORE any startup DDL, seed or repair.

Both EXPECTED_DATABASE_NAME and EXPECTED_DATABASE_HOST must be explicitly
configured for each environment. A matching name/schema/host does not prove
physical instance identity, persistence, or a recoverable backup.
"""
import os
import psycopg
from psycopg.conninfo import conninfo_to_dict
from ops.p0_db_identity_preflight import QUERY, evaluate


def verify_prewrite_database(database_url, expected_name, expected_host, connect=None):
    """Raise a sanitized error on any ambiguity; never write or print secrets."""
    blocked = RuntimeError("P0 startup blocked: database preflight not verified")
    if not all(isinstance(v, str) and v.strip()
               for v in (database_url, expected_name, expected_host)):
        raise blocked
    try:
        params = conninfo_to_dict(database_url)
        host = params.get("host", "").lower().rstrip(".")
        expected = expected_host.strip().lower().rstrip(".")
        # libpq hostaddr/service can silently redirect a connection elsewhere.
        if (not host or host != expected or
                params.get("hostaddr") or params.get("service") or
                params.get("servicefile") or os.getenv("PGHOSTADDR") or
                os.getenv("PGSERVICE")):
            raise blocked
        connector = connect if connect is not None else psycopg.connect
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
    verify_prewrite_database(
        os.getenv("DATABASE_URL", ""),
        os.getenv("EXPECTED_DATABASE_NAME", ""),
        os.getenv("EXPECTED_DATABASE_HOST", ""),
    )
