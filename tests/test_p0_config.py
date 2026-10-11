"""P0 configuration contract: no network or database writes."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "main.py").read_text(encoding="utf-8")

def test_database_url_is_required():
    tree = ast.parse(source)
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "db"]
    assert functions, "db() must exist"
    body = ast.get_source_segment(source, functions[0]) or ""
    assert "DATABASE_URL" in body
    assert "raise RuntimeError" in body

def test_no_credentials_committed_to_config():
    text = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "postgresql://" not in text
    assert "WERO_ADMIN_TOKEN" in text
