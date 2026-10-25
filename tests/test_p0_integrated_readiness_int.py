"""Static and pure integration gates for ranking, INT and PostgreSQL readiness.

These tests do not access production, call HTTP endpoints or create events.
"""
import ast
from pathlib import Path

from int_qualification import filter_int_qualified_offers
from p0_readiness import readiness_http_status


def test_int_gate_and_db_readiness_both_fail_closed():
    public_clicks = [{"offer_id": 4, "clicks_7d": 7}]
    forged = {4: {"source_authenticated": True, "int1_score": 100, "int2_score": 100}}
    assert filter_int_qualified_offers(public_clicks, forged) == []
    assert readiness_http_status({"status": "degraded", "database_ok": False,
                                  "storage_persistent": False}) == 503
    assert readiness_http_status({"status": "ok", "database_ok": True,
                                  "storage_persistent": True}) == 503
    assert readiness_http_status({"status": "ok", "database_ok": True,
                                  "storage_persistent": True}, True) == 200


def test_integrated_route_and_rank_contracts_exist():
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert {"ready", "health", "premium_ai_ranking", "go_offer_landing", "confirm_offer_click"} <= set(functions)
    ready = ast.get_source_segment(source, functions["ready"])
    rank = ast.get_source_segment(source, functions["premium_ai_ranking"])
    assert 'report = health()' in ready
    assert 'readiness_http_status(report, identity_ok)' in ready
    assert 'database_identity_verified(cur.fetchone(), expected_name)' in ready
    assert '"offers": qualified_offers' in rank
    assert '"consultative_offers": offers' in rank
    assert 'COUNT(c.id) FILTER (WHERE c.created_at >= NOW() - INTERVAL \'7 days\') > 0' in rank
