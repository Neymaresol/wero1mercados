"""Offline P0 regression: never promote untrusted INT.1/INT.2 signals.

This test does not import the web app, access databases, make HTTP requests,
or create visits, clicks, conversions, sales, or payments.
"""
import ast
from pathlib import Path

from int_qualification import INT_GATE_STATUS, filter_int_qualified_offers


def test_caller_supplied_int_scores_and_auth_flags_never_qualify():
    offers = [
        {"offer_id": 1, "active": True, "int1": 100, "int2": 100},
        {"offer_id": 2, "active": True, "int1": 0, "int2": 0},
    ]
    spoofed_evidence = {
        1: {"source_authenticated": True, "trusted": True, "int2": 100},
        2: {"source_authenticated": True, "trusted": True, "int1": 1},
    }
    assert INT_GATE_STATUS == "BLOCKED_NO_VERIFIED_EVENT_PIPELINE"
    assert filter_int_qualified_offers(offers, spoofed_evidence) == []
    assert filter_int_qualified_offers(offers) == []


def test_premium_ranking_keeps_unverified_clicks_consultative_only():
    tree = ast.parse((Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8"))
    endpoint = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "premium_ai_ranking"
    )
    returns = [node.value for node in ast.walk(endpoint) if isinstance(node, ast.Return)]
    assert len(returns) == 1 and isinstance(returns[0], ast.Dict)
    fields = {
        key.value: value
        for key, value in zip(returns[0].keys, returns[0].values)
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert isinstance(fields.get("offers"), ast.Name)
    assert fields["offers"].id == "qualified_offers"
    assert isinstance(fields.get("consultative_offers"), ast.Name)
    assert fields["consultative_offers"].id == "offers"
    assert isinstance(fields.get("publication_status"), ast.Name)
    assert fields["publication_status"].id == "INT_GATE_STATUS"
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "filter_int_qualified_offers"
        for node in ast.walk(endpoint)
    )
