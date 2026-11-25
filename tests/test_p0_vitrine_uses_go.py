"""P0 regression tests for safe Werozinha landing entry points.

Static contract only: no database writes, HTTP requests, clicks or conversions.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def function_source(name):
    node = next(
        item for item in TREE.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == name
    )
    return ast.get_source_segment(SOURCE, node)


def test_legacy_amazon_entry_redirects_to_safe_landing_without_counting_click():
    body = function_source("werozinha_one_click_amazon")
    assert 'landing = f"/go/{offer_id}?' in body
    assert "RedirectResponse(landing, status_code=302)" in body
    assert "INSERT INTO clicks" not in body
    assert "amazon_affiliate_tag" in body


def test_vitrine_cards_point_directly_to_go_landing():
    body = function_source("werozinha_amazon_campaign")
    assert 'target = "/go/" + str(int(item["id"]))' in body
    assert 'target = "/campanha/werozinha/amazon/"' not in body
