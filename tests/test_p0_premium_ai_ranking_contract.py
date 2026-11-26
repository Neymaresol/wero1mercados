"""P0 regression coverage for the premium AI ranking's zero/stale-click exclusion.
Static/offline checks only; no database or network calls.
"""
from pathlib import Path
import ast

SOURCE = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")
ast.parse(SOURCE)


def ranking_source():
    fragment = SOURCE.split("def premium_ai_ranking(", 1)[1]
    return fragment.split("\n@app.", 1)[0]


def test_ranking_excludes_offers_without_any_real_click():
    fragment = ranking_source()
    assert "HAVING COUNT(c.id) > 0" in fragment


def test_ranking_requires_recent_click_within_seven_days():
    fragment = ranking_source()
    assert "COUNT(c.id) FILTER (WHERE c.created_at >= NOW() - INTERVAL '7 days') > 0" in fragment


def test_ranking_remains_read_only_and_advisory():
    fragment = ranking_source()
    assert "INSERT INTO" not in fragment
    assert "UPDATE offers" not in fragment
    assert "mode": "read_only" in SOURCE or '"mode": "read_only"' in SOURCE
