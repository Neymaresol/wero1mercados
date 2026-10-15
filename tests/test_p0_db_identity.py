import ast
from pathlib import Path


def test_db_identity_route_requires_admin_and_avoids_secrets():
    tree = ast.parse(Path("main.py").read_text(encoding="utf-8"))
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "p0_db_identity")
    args = {arg.arg for arg in fn.args.args}
    assert "_admin" in args
    source = ast.get_source_segment(Path("main.py").read_text(encoding="utf-8"), fn)
    assert "Depends(require_admin)" in source
    assert "current_database()" in source
    assert "hmac.new" in source
    assert "DATABASE_URL" not in source
    assert "SELECT " in source
