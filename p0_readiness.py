"""Pure fail-closed readiness decision. No database or network dependencies."""


def readiness_http_status(report):
    """Return HTTP 200 only when DB connectivity and durability are explicitly verified.

    A successful SELECT 1 or an unverified storage_persistent label must not
    qualify the service as ready. Verification is an independent requirement.
    """
    if not isinstance(report, dict):
        return 503
    if (report.get("status") == "ok"
            and report.get("database_ok") is True
            and report.get("storage_persistent") is True
            and report.get("storage_persistence_verified") is True):
        return 200
    return 503
