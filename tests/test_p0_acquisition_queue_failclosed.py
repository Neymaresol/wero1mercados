"""Offline P0 regression: clicks cannot populate an auto-actionable campaign queue.

This test reads source only. It never imports the app, opens HTTP, connects to
a database, posts on social networks, or creates commercial events.
"""
import ast
from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")


def _acquisition():
    tree = ast.parse(SOURCE)
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == "acquisition")


def test_acquisition_queue_fails_closed_without_authenticated_int():
    fn = _acquisition()
    result = next(n.value for n in fn.body if isinstance(n, ast.Return))
    assert isinstance(result, ast.Dict)
    fields = {k.value: v for k, v in zip(result.keys, result.values)
              if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    assert isinstance(fields["campaign_queue"], ast.List)
    assert fields["campaign_queue"].elts == []
    assert isinstance(fields["campaign_queue_status"], ast.Name)
    assert fields["campaign_queue_status"].id == "INT_GATE_STATUS"
    assert isinstance(fields["consultative_queue"], ast.Name)
    assert fields["consultative_queue"].id == "queue"
    assert isinstance(fields["publication_allowed"], ast.Constant)
    assert fields["publication_allowed"].value is False


def test_unverified_click_candidates_are_explicitly_advisory():
    fn = _acquisition()
    text = ast.get_source_segment(SOURCE, fn)
    for marker in (
        '"signal_basis":"unverified_outbound_clicks"',
        '"int1_verified":False',
        '"int2_verified":False',
        '"publication_allowed":False',
        '"requires_manual_review":True',
    ):
        assert marker in text
    assert "INSERT INTO" not in text
    assert "UPDATE offers" not in text


def test_qualified_ranking_stays_separate():
    tree = ast.parse(SOURCE)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == "premium_ai_ranking")
    text = ast.get_source_segment(SOURCE, fn)
    assert "qualified_offers = filter_int_qualified_offers(offers)" in text
    assert '"offers": qualified_offers' in text
