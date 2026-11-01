"""Offline P0 contracts; no HTTP, DB writes, clicks, conversions or sales."""
import ast
from pathlib import Path

from int_qualification import INT_GATE_STATUS, filter_int_qualified_offers

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def endpoint(name):
    return next(
        node for node in TREE.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


def route(fn):
    for decorator in fn.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.args
            and isinstance(decorator.args[0], ast.Constant)
        ):
            return decorator.func.attr, decorator.args[0].value
    raise AssertionError("Endpoint has no recognized HTTP route")


def body(fn):
    return ast.get_source_segment(SOURCE, fn)


def test_int_gate_ignores_forged_scores_and_auth_flags():
    offers = [{"offer_id": 1, "int1": 100, "int2": 100, "active": True}]
    forged = {1: {"source_authenticated": True, "trusted": True, "event_ids": ["a", "b"]}}
    assert INT_GATE_STATUS == "BLOCKED_NO_VERIFIED_EVENT_PIPELINE"
    assert filter_int_qualified_offers(offers, forged) == []
    assert filter_int_qualified_offers(offers) == []


def test_premium_ranking_separates_int_from_consultative_clicks():
    fn = endpoint("premium_ai_ranking")
    returns = [node.value for node in fn.body if isinstance(node, ast.Return)]
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
    assert "filter_int_qualified_offers" in body(fn)


def test_go_get_excludes_declared_prefetch_and_never_counts_clicks():
    fn = endpoint("go_offer_landing")
    assert route(fn) == ("get", "/go/{offer_id}")
    source = body(fn)
    assert "should_count_landing_visit(request.headers)" in source
    assert "INSERT INTO offer_landing_visits" in source
    assert "INSERT INTO clicks" not in source


def test_out_click_boundary_is_post_and_validates_affiliate():
    fn = endpoint("confirm_offer_click")
    assert route(fn) == ("post", "/out/{offer_id}")
    source = body(fn)
    assert "validate_authorized_url" in source
    assert "require_affiliate_attribution" in source
    assert "INSERT INTO clicks" in source


def test_legacy_amazon_get_redirects_without_counting_click():
    fn = endpoint("werozinha_one_click_amazon")
    assert route(fn) == ("get", "/campanha/werozinha/amazon/{offer_id}")
    source = body(fn)
    assert "INSERT INTO clicks" not in source
    assert "RedirectResponse(landing" in source
    assert 'landing = f"/go/{offer_id}' in source
