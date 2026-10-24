"""Regression contract: premium ranking cannot promote zero-engagement offers.

Static verification only; does not touch HTTP redirect routes, databases or production.
"""
import ast
from pathlib import Path


def test_premium_ranking_filters_zero_clicks_and_recent_zeroes():
    source = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "premium_ai_ranking")
    body = ast.get_source_segment(source, func)
    assert body is not None
    assert "HAVING COUNT(c.id) > 0" in body
    assert "COUNT(c.id) FILTER (WHERE c.created_at >= NOW() - INTERVAL '7 days') > 0" in body
    assert "LEFT JOIN clicks c ON c.offer_id=o.id" in body
    assert "Depends(require_admin)" in body
    assert "INSERT INTO" not in body
    assert "UPDATE offers" not in body
