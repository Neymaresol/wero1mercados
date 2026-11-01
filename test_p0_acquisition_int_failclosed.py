"""Offline regression: public clicks must never become INT-qualified campaign work."""
import ast
from pathlib import Path

from int_qualification import INT_GATE_STATUS, filter_int_qualified_offers


def _function_source(name: str) -> str:
    source = Path("main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        item for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == name
    )
    return ast.get_source_segment(source, node)


def test_int_gate_ignores_clicks_and_caller_supplied_flags():
    offers = [{
        "offer_id": 7,
        "tracked_clicks": 999,
        "clicks_7d": 999,
        "int1_verified": True,
        "int2_verified": True,
        "source_authenticated": True,
    }]
    evidence = {7: {"int1": True, "int2": True, "source_authenticated": True}}
    assert filter_int_qualified_offers(offers, evidence_by_offer=evidence) == []
    assert INT_GATE_STATUS == "BLOCKED_NO_VERIFIED_EVENT_PIPELINE"


def test_acquisition_queue_stays_empty_without_authenticated_int():
    body = _function_source("acquisition")
    assert '"campaign_queue": []' in body
    assert '"campaign_queue_status": INT_GATE_STATUS' in body
    assert '"consultative_queue": consultative_queue' in body
    assert '"publication_allowed": False' in body
    assert '"requires_manual_review": True' in body
    assert '"int1_verified": False' in body
    assert '"int2_verified": False' in body
    assert '"signal_basis": "unverified_outbound_clicks"' in body
    assert "INTERVAL '7 days'" in body


def test_premium_ranking_separates_int_from_recent_consultative_clicks():
    body = _function_source("premium_ai_ranking")
    assert "filter_int_qualified_offers(offers)" in body
    assert '"offers": qualified_offers' in body
    assert '"consultative_offers": offers' in body
    assert "HAVING COUNT(c.id) > 0" in body
    assert "INTERVAL '7 days'" in body
