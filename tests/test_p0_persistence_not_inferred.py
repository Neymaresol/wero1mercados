"""P0 offline regression: SELECT 1 is connectivity, never persistence proof.

This test never imports the web app, connects to databases or calls commercial routes.
"""
import ast
from pathlib import Path

from p0_readiness import readiness_http_status


SOURCE = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")


def _health_result_fields():
    tree = ast.parse(SOURCE)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "health")
    returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
    assert len(returns) == 1
    result = returns[0].value
    assert isinstance(result, ast.Dict)
    return {
        k.value: v
        for k, v in zip(result.keys, result.values)
        if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }


def test_connectivity_cannot_claim_persistence():
    fields = _health_result_fields()
    assert isinstance(fields["storage_persistent"], ast.Constant)
    assert fields["storage_persistent"].value is None
    assert isinstance(fields["persistence_verification"], ast.Constant)
    assert fields["persistence_verification"].value == "NOT_VERIFIED"
    assert isinstance(fields["health_scope"], ast.Constant)
    assert fields["health_scope"].value == "db_connectivity_only"
    assert isinstance(fields["database_ok"], ast.Name)
    assert fields["database_ok"].id == "database_ok"


def test_readiness_rejects_unknown_persistence_even_when_db_responds():
    report = {
        "status": "ok", "database_ok": True,
        "storage_persistent": None, "persistence_verification": "NOT_VERIFIED",
    }
    assert readiness_http_status(report) == 503
    assert readiness_http_status({**report, "storage_persistent": False}) == 503
    assert readiness_http_status({**report, "database_ok": False}) == 503


def test_no_runtime_claim_of_verified_backup_or_restore():
    fields = _health_result_fields()
    assert "backup_restored" not in fields
    assert "restore_verified" not in fields
    assert "database_identity_verified" not in fields
