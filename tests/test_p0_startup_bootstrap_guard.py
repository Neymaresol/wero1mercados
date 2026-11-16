"""Regression tests for the production-safe database bootstrap boundary."""
import ast
from pathlib import Path


def _module():
    source = Path("main.py").read_text(encoding="utf-8")
    return source, ast.parse(source)


def _function(tree, name):
    return next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


def test_startup_database_mutations_require_explicit_staging_opt_in():
    _, tree = _module()
    gate = _function(tree, "startup_bootstrap_enabled")
    source = ast.get_source_segment(Path("main.py").read_text(encoding="utf-8"), gate)

    assert 'deployment_env == "staging"' in source
    assert 'explicit_opt_in in {"1", "true", "yes"}' in source
    assert 'WERO_MODE != "production"' in source


def test_startup_returns_before_ddl_and_seeds_when_gate_is_closed():
    _, tree = _module()
    startup = _function(tree, "startup")

    assert startup.body
    guard = startup.body[0]
    assert isinstance(guard, ast.If)
    assert isinstance(guard.test, ast.UnaryOp)
    assert isinstance(guard.test.op, ast.Not)
    assert isinstance(guard.test.operand, ast.Call)
    assert isinstance(guard.test.operand.func, ast.Name)
    assert guard.test.operand.func.id == "startup_bootstrap_enabled"
    assert len(guard.body) == 1
    assert isinstance(guard.body[0], ast.Return)

    calls = [
        node.value.func.id
        for node in startup.body[1:]
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
    ]
    assert calls == ["init_db", "seed_amazon_campaigns", "seed_additional_amazon_campaigns"]
