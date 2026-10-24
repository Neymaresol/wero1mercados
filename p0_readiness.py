"""Pure fail-closed readiness decision. No database or network dependencies."""


def readiness_http_status(report):
    """Return HTTP 200 only for explicit, internally consistent DB health."""
    if not isinstance(report, dict):
        return 503
    if (report.get("status") == "ok"
            and report.get("database_ok") is True
            and report.get("storage_persistent") is True):
        return 200
    return 503
