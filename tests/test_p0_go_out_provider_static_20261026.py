"""Static P0 route-contract checks; never import app or issue HTTP/SQL writes.

These checks protect the documented two-step affiliate flow while integrated
staging HTTP tests and authenticated partner reconciliation remain blocked.
"""
import ast
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _function(name):
    return next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == name)


def _routes(fn):
    found = []
    for decorator in fn.decorator_list:
        if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
            continue
        if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
            continue
        found.append((decorator.func.attr, decorator.args[0].value))
    return found


def _body(fn):
    return ast.get_source_segment(SOURCE, fn)


def test_go_is_landing_get_and_out_is_explicit_post():
    assert ("get", "/go/{offer_id}") in _routes(_function("go_offer_landing"))
    assert ("post", "/out/{offer_id}") in _routes(_function("confirm_offer_click"))
    assert ("get", "/out/{offer_id}") not in _routes(_function("confirm_offer_click"))
    assert ("post", "/go/{offer_id}") not in _routes(_function("go_offer_landing"))


def test_partner_validation_precedes_tracking_in_both_routes():
    for name, marker in (
        ("go_offer_landing", "INSERT INTO offer_landing_visits"),
        ("confirm_offer_click", "INSERT INTO clicks"),
    ):
        body = _body(_function(name))
        assert body.index("classify_channel(channel)") < body.index(marker)
        assert body.index("safe_campaign(campaign)") < body.index(marker)
        assert body.index("validate_authorized_url(") < body.index(marker)
        assert body.index("require_affiliate_attribution(") < body.index(marker)
        assert "INSERT INTO conversions" not in body


def test_out_redirect_only_after_explicit_click():
    landing = _body(_function("go_offer_landing"))
    outbound = _body(_function("confirm_offer_click"))
    assert '<form method="post" action="/out/' in landing
    assert "RedirectResponse(" not in landing
    assert "RedirectResponse(target, status_code=303)" in outbound


def test_legacy_conversion_ingest_rejects_unverified_provenance_before_db_write():
    body = _body(_function("ingest_provider_conversion"))
    assert body.index("reject_unverified_manual_conversion()") < body.index("INSERT INTO conversions")
    assert "status_code=403" in body
