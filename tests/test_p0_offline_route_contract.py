"""Offline P0 contracts for outbound attribution and conversion provenance.

Static inspection only: does not import the app, open HTTP connections,
write to databases, or manufacture visits, clicks, sales or payments.
"""
import ast
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
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


def test_get_landing_does_not_count_clicks_and_checks_prefetch():
    fn = endpoint("go_offer_landing")
    assert route(fn) == ("get", "/go/{offer_id}")
    source = body(fn)
    assert "INSERT INTO clicks" not in source
    assert "should_count_landing_visit(request.headers)" in source
    assert "INSERT INTO offer_landing_visits" in source
    assert 'method="post"' in source
    assert "/out/{offer_id}" in source


def test_outbound_click_requires_post_and_affiliate_checks():
    fn = endpoint("confirm_offer_click")
    assert route(fn) == ("post", "/out/{offer_id}")
    source = body(fn)
    assert "validate_authorized_url" in source
    assert "require_affiliate_attribution" in source
    assert "INSERT INTO clicks" in source


def test_legacy_amazon_get_never_inserts_click():
    fn = endpoint("werozinha_one_click_amazon")
    assert route(fn) == ("get", "/campanha/werozinha/amazon/{offer_id}")
    source = body(fn)
    assert "INSERT INTO clicks" not in source
    assert "RedirectResponse(landing" in source
    assert 'landing = f"/go/{offer_id}' in source


def test_manual_provider_conversion_fails_closed():
    fn = endpoint("ingest_provider_conversion")
    assert route(fn) == ("post", "/api/commercial/conversions/provider")
    source = body(fn)
    assert "reject_unverified_manual_conversion()" in source
    assert "status_code=403" in source
