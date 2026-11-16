"""Regression tests for the consultative ranking and INT qualification boundary.

The public-click ranking is not authenticated INT evidence. Zero/stale-click
offers must not enter the consultative list, and the INT-qualified list stays
empty until an independently authenticated server-side event pipeline exists.
"""
import ast
from pathlib import Path


def _function_source(name: str) -> str:
    source = Path("main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        item for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == name
    )
    return ast.get_source_segment(source, node)


def test_consultative_ranking_excludes_zero_and_stale_click_offers():
    body = _function_source("premium_ai_ranking")

    assert "{VERIFIED_OFFER_JOIN_SQL}" in body
    assert "HAVING COUNT(c.id) > 0" in body
    assert (
        "COUNT(c.id) FILTER "
        "(WHERE c.created_at >= NOW() - INTERVAL '7 days') > 0"
    ) in body
    assert '"consultative_offers": offers' in body
    assert '"offers": qualified_offers' in body
    assert "NOT INT-qualified" in body


def test_int_qualification_remains_blocked_without_verified_event_pipeline():
    from int_qualification import INT_GATE_STATUS, filter_int_qualified_offers

    assert INT_GATE_STATUS == "BLOCKED_NO_VERIFIED_EVENT_PIPELINE"
    assert filter_int_qualified_offers(
        [{"offer_id": 1, "clicks_7d": 12, "int1": 0, "int2": 0}],
        evidence_by_offer={1: {"verified": True, "int1": 99, "int2": 99}},
    ) == []
