"""Read-only PARADIGMA database identity/schema preflight.

Run with DATABASE_URL supplied through a secure environment variable:
    EXPECTED_DATABASE_NAME=wero1mercados python ops/p0_db_identity_preflight.py

This does NOT prove durable storage, the application's actual DATABASE_URL,
or backup/restore safety. No connection string or exception detail is printed.
"""
import json
import os

REQUIRED_TABLES = ("offers", "clicks", "conversions", "offer_landing_visits")
QUERY = "SELECT current_database(), " + ", ".join(
    "to_regclass('public." + name + "') IS NOT NULL" for name in REQUIRED_TABLES
)


def evaluate(row, expected_database):
    """Sanitized fail-closed verdict from a read-only SELECT tuple."""
    if not expected_database or not isinstance(row, (tuple, list)) or len(row) != 1 + len(REQUIRED_TABLES):
        return {"status": "blocked", "database_name_match": False, "missing_tables": list(REQUIRED_TABLES)}
    name_ok = isinstance(row[0], str) and row[0] == expected_database
    missing = [table for table, exists in zip(REQUIRED_TABLES, row[1:]) if exists is not True]
    return {"status": "pass" if name_ok and not missing else "blocked",
            "database_name_match": name_ok, "missing_tables": missing,
            "scope": "read_only_identity_and_schema_not_durability"}


def main():
    expected = os.environ.get("EXPECTED_DATABASE_NAME", "").strip()
    database_url = os.environ.get("DATABASE_URL", "")
    if not expected or not database_url:
        print(json.dumps({"status": "blocked", "reason": "required_environment_missing"}))
        return 2
    try:
        import psycopg
        with psycopg.connect(database_url, connect_timeout=5,
                             options="-c default_transaction_read_only=on") as conn:
            with conn.cursor() as cur:
                cur.execute(QUERY)
                result = evaluate(cur.fetchone(), expected)
    except Exception:
        # Never echo exceptions: drivers may embed connection details.
        print(json.dumps({"status": "blocked", "reason": "database_probe_failed"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
