"""Offline readiness tests; no application import, DB access, or writes."""

from p0_readiness import readiness_http_status


def test_reachable_database_is_ready_while_backup_restore_is_unverified():
    report = {
        "status": "ok",
        "database_reachable": True,
        "database_ok": True,
        "storage_persistent": None,
        "storage_persistence_verified": False,
        "storage_persistence_status": "NOT_VERIFIED",
    }
    assert readiness_http_status(report) == 200


def test_unreachable_database_is_not_ready():
    report = {
        "status": "degraded",
        "database_reachable": False,
        "database_ok": False,
        "storage_persistent": None,
    }
    assert readiness_http_status(report) == 503


def test_explicit_unreachable_flag_overrides_legacy_database_ok():
    report = {
        "status": "ok",
        "database_reachable": False,
        "database_ok": True,
        "storage_persistent": True,
    }
    assert readiness_http_status(report) == 503


def test_legacy_health_payload_remains_supported():
    report = {
        "status": "ok",
        "database_ok": True,
        "storage_persistent": True,
    }
    assert readiness_http_status(report) == 200


def test_missing_or_inconsistent_health_fails_closed():
    for report in (None, {}, {"status": "ok"}, {"status": "degraded", "database_reachable": True}):
        assert readiness_http_status(report) == 503
