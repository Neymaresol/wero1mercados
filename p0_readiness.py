"""Pure fail-closed readiness and PostgreSQL identity decisions.

No database connections, writes or network operations are performed here.
The identity gate checks a configured database name and required tables; it
does not establish a cloud instance ID, durable storage or restore safety.
"""

REQUIRED_TABLES = ("offers", "clicks", "conversions", "offer_landing_visits")


def database_identity_verified(row, expected_name):
    """Require a configured database name and all four schema markers."""
    if not expected_name or not isinstance(row, dict):
        return False
    if row.get("database_name") != expected_name:
        return False
    return all(row.get(table) is True for table in REQUIRED_TABLES)


def readiness_http_status(report, identity_verified=False):
    """Return HTTP 200 only for healthy DB plus independently checked identity."""
    if not isinstance(report, dict):
        return 503
    if (report.get("status") == "ok"
            and report.get("database_ok") is True
            and report.get("storage_persistent") is True
            and identity_verified is True):
        return 200
    return 503
