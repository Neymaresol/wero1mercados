"""Fail-closed HTTP readiness decision independent of backup verification."""


def readiness_http_status(report):
    """Return 200 only when the health report confirms a reachable database.

    Backup/restore proof is reported separately by /health. It must not be
    conflated with runtime readiness: NOT_VERIFIED is not the same as offline.
    """
    if not isinstance(report, dict) or report.get("status") != "ok":
        return 503

    if "database_reachable" in report:
        reachable = report.get("database_reachable") is True
    else:
        # Backward compatibility for health payloads before database_reachable.
        reachable = report.get("database_ok") is True

    return 200 if reachable else 503
