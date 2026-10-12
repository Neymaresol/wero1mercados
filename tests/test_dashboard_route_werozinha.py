import ast
from pathlib import Path


def test_dashboard_and_avatar_routes_are_separate():
    tree = ast.parse(Path('main.py').read_text(encoding='utf-8'))
    routes = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and decorator.args and isinstance(decorator.args[0], ast.Constant):
                    routes[decorator.args[0].value] = node.name
    assert routes['/dashboard'] == 'dashboard'
    assert routes['/assets/werozinha-avatar.svg'] == 'werozinha_avatar'
    assert routes['/dashboard'] != routes['/assets/werozinha-avatar.svg']
