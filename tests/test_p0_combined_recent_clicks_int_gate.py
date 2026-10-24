"""Combined P0 regression: recent engagement never becomes authenticated INT.

Static-only route verification and pure fail-closed unit checks. These tests
never call /go, /out, live databases, social networks or financial providers.
"""
import ast
from pathlib import Path

from int_qualification import INT_GATE_STATUS, filter_int_qualified_offers

SOURCE = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")


def test_recent_click_sql_gate_is_present():
    tree = ast.parse(SOURCE)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == "premium_ai_ranking")
    body = ast.get_source_segment(SOURCE, fn)
    assert "HAVING COUNT(c.id) > 0" in body
    assert "COUNT(c.id) FILTER (WHERE c.created_at >= NOW() - INTERVAL '7 days') > 0" in body
    assert "Depends(require_admin)" in body
    assert "qualified_offers = filter_int_qualified_offers(offers)" in body
    assert '"offers": qualified_offers' in body
    assert "INSERT INTO" not in body
    assert "UPDATE offers" not in body


def test_clicks_and_caller_claims_cannot_qualify_int():
    offers = [{"offer_id": 4, "tracked_clicks": 82, "clicks_7d": 10}]
    forged = {4: {"source_authenticated": True, "int1_score": 100,
                  "int2_score": 100, "int1_event_id": "forged-1",
                  "int2_event_id": "forged-2"}}
    assert filter_int_qualified_offers(offers, forged) == []
    assert filter_int_qualified_offers(offers) == []
    assert INT_GATE_STATUS == "BLOCKED_NO_VERIFIED_EVENT_PIPELINE"
    assert offers[0]["tracked_clicks"] == 82
