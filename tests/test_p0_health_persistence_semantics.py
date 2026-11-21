"""P0 health contract: reachability is not proof of durable persistence."""
import ast
from pathlib import Path


def test_health_does_not_claim_persistence_from_select_one():
    source = Path("main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    health = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "health"
    )
    body = ast.get_source_segment(source, health)
    assert 'cur.execute("SELECT 1")' in body
    assert '"database_reachable": database_ok' in body
    assert '"storage_persistent": None' in body
    assert '"storage_persistence_verified": False' in body
    assert '"storage_persistence_status": "NOT_VERIFIED"' in body
    assert '"storage_persistent": database_ok' not in body
