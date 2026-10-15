"""P0: acquisition ranking must not promote zero-interaction offers.

Static regression contract. No database writes, clicks, or synthetic conversions.
"""
import ast
from pathlib import Path


def test_acquisition_ranking_requires_observed_clicks():
    source = Path("main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "acquisition")
    body = ast.get_source_segment(source, function)
    assert body is not None
    # Eligibility is not engagement: zero-click offers must be excluded from
    # the priority campaign queue until explicitly handled as exploration.
    assert "COUNT(c.id) AS clicks" in body
    assert "HAVING COUNT(C.ID) > 0" in body.upper() or "if int(r[\"clicks\"]) > 0" in body
