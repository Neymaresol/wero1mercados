from pathlib import Path
import ast

source = Path(__file__).resolve().parents[1].joinpath("main.py").read_text()
ast.parse(source)

def test_ranking_is_admin_only():
    assert 'def premium_ai_ranking(' in source
    fragment = source.split('def premium_ai_ranking(', 1)[1]
    assert '_admin: None = Depends(require_admin)' in fragment.split('):', 1)[0]

def test_ranking_is_read_only():
    fragment = source.split('def premium_ai_ranking(', 1)[1]
    assert 'FROM offers o' in fragment
    assert 'LEFT JOIN clicks c ON c.offer_id=o.id' in fragment
    assert 'INSERT INTO' not in fragment
    assert 'UPDATE offers' not in fragment
    assert 'NOT_CONNECTED' in fragment
