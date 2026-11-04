"""Static financial source contract; no production DB access."""
import re
from pathlib import Path

s=(Path(__file__).resolve().parents[1]/"main.py").read_text()


def test_only_provider_confirmed_sales():
    assert "FROM conversions WHERE status='confirmed'" in s
    assert 'confirmed_commission_brl' in s
    assert 'offer_landing_visits' in s


def test_separate_clicks_and_sales():
    assert re.search(r'"tracked_clicks"\s*:\s*clicks', s)
    assert re.search(r'"confirmed_sales"\s*:\s*sales', s)
