"""Static regressions for truthful persistence health and GET-side click safety."""
import ast
from pathlib import Path


def _source():
    return Path("main.py").read_text(encoding="utf-8")


def _function_source(name: str) -> str:
    source = _source()
    tree = ast.parse(source)
    node = next(
        item for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == name
    )
    return ast.get_source_segment(source, node)


def _is_app_get(node) -> bool:
    for decorator in node.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "app"
            and decorator.func.attr == "get"
        ):
            return True
    return False


def test_health_never_equates_select_one_with_durable_persistence():
    body = _function_source("health")

    assert 'cur.execute("SELECT 1")' in body
    assert '"database_reachable": database_ok' in body
    assert '"storage_persistent": None' in body
    assert '"storage_persistence_verified": False' in body
    assert '"storage_persistence_status": "NOT_VERIFIED"' in body
    assert '"storage_persistence_note":' in body
    assert '"storage_persistent": database_ok' not in body


def test_get_routes_never_insert_outbound_clicks():
    source = _source()
    tree = ast.parse(source)
    offenders = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_app_get(node):
            body = ast.get_source_segment(source, node) or ""
            if "INSERT INTO clicks" in body:
                offenders.append(node.name)

    assert offenders == [], (
        "GET handlers must not create outbound-click records; "
        "use the token-bound POST /out flow instead: " + ", ".join(offenders)
    )
