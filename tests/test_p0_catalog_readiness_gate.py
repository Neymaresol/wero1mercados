"""P0/P1 regression: no stale or unverified offer reaches public catalog paths."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTION_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)


def function(name):
    return next(
        node for node in TREE.body
        if isinstance(node, FUNCTION_TYPES) and node.name == name
    )


def source_of(name):
    return ast.get_source_segment(SOURCE, function(name))


def test_shared_provider_readiness_gate_is_fail_closed():
    assert "po.available = TRUE" in SOURCE
    assert "po.price_brl > 0" in SOURCE
    assert "po.source_updated_at IS NOT NULL" in SOURCE
    assert "po.source_updated_at >= NOW() - INTERVAL '7 days'" in SOURCE


def test_public_offer_paths_require_the_shared_readiness_join():
    for name in (
        "public_catalog",
        "list_offers",
        "authorized_storefront_trends",
        "go_offer_landing",
        "confirm_offer_click",
        "acquisition",
        "commercial",
        "catalog_levels",
        "ai_campaign_briefs",
        "premium_ai_ranking",
        "werozinha_one_click_amazon",
        "werozinha_amazon_campaign",
    ):
        assert "VERIFIED_OFFER_JOIN_SQL" in source_of(name), name


def test_products_api_uses_matching_ready_offer_and_partner_rows():
    code = source_of("list_products")
    assert "JOIN product_offers po ON po.product_id=pr.id" in code
    assert "JOIN partners p ON p.id=po.partner_id" in code
    assert "JOIN offers o ON o.product_id=pr.id" in code
    assert "po.available=TRUE" in code
    assert "po.price_brl > 0" in code
    assert "po.source_updated_at >= NOW() - INTERVAL '7 days'" in code


def test_manual_admin_registration_never_claims_provider_verification():
    code = source_of("register_commercial_offer")
    assert "manual_admin_unverified" in code
    assert "source_updated_at=NULL" in code
    assert "available,active,source_updated_at" in code
    assert "FALSE,TRUE,NULL" in code


def test_financial_confirmation_route_is_not_confused_with_catalog_readiness():
    code = source_of("ingest_provider_conversion")
    assert "provider" in code.lower()
    assert "VERIFIED_OFFER_JOIN_SQL" not in code
    assert "conversion" in code.lower()
