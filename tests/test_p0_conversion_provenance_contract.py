"""P0 regressions for authenticated affiliate-conversion provenance.

These tests exercise only rejection paths and static control flow. They do not
create, persist, or simulate any sale, click, conversion, or commission.
"""
import ast
from pathlib import Path

from p0_conversion_gate import reject_unverified_manual_conversion, verified_rows
from provider_reconciliation import Provenance


def _function(tree, name):
    return next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


def test_manual_conversion_endpoint_gate_rejects_unverified_input():
    try:
        reject_unverified_manual_conversion()
    except PermissionError as exc:
        assert "not authenticated partner evidence" in str(exc)
    else:
        raise AssertionError("manual conversion must remain fail-closed")


def test_verified_rows_rejects_caller_supplied_mapping_as_provenance():
    try:
        verified_rows(
            partner="amazon",
            raw=b"",
            provenance={"partner": "amazon", "verified": True},
            columns={},
        )
    except ValueError as exc:
        assert "authenticated partner provenance required" in str(exc)
    else:
        raise AssertionError("a request-shaped mapping is not Provenance")


def test_verified_rows_rejects_unverified_provenance_before_parsing():
    provenance = Provenance(
        partner="amazon",
        account_id="account-reference",
        report_id="report-reference",
        sha256="0" * 64,
        verified=False,
    )
    try:
        verified_rows(
            partner="amazon",
            raw=b"",
            provenance=provenance,
            columns={},
        )
    except ValueError as exc:
        assert "authenticated partner provenance required" in str(exc)
    else:
        raise AssertionError("unverified provenance must be rejected")


def test_verified_rows_rejects_partner_identity_mismatch():
    provenance = Provenance(
        partner="shopee",
        account_id="account-reference",
        report_id="report-reference",
        sha256="0" * 64,
        verified=True,
    )
    try:
        verified_rows(
            partner="amazon",
            raw=b"",
            provenance=provenance,
            columns={},
        )
    except ValueError as exc:
        assert "partner identity mismatch" in str(exc)
    else:
        raise AssertionError("cross-partner provenance must be rejected")


def test_provider_conversion_route_rejects_before_database_access():
    source = Path("main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    route = _function(tree, "ingest_provider_conversion")

    gate_lines = [
        node.lineno for node in ast.walk(route)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "reject_unverified_manual_conversion"
    ]
    db_lines = [
        node.lineno for node in ast.walk(route)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "db"
    ]

    assert gate_lines, "conversion route must call the fail-closed provenance gate"
    assert db_lines, "conversion route database access must remain visible to this test"
    assert min(gate_lines) < min(db_lines), "reject unverified input before any database access"
