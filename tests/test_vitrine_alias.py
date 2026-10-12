from pathlib import Path
import ast


def test_vitrine_alias_points_to_existing_campaign():
    tree = ast.parse(Path('main.py').read_text(encoding='utf-8'))
    routes = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and decorator.args and isinstance(decorator.args[0], ast.Constant):
                    routes[decorator.args[0].value] = node.name
    assert routes['/vitrine'] == routes['/campanha/werozinha']
    assert Path('static/werozinha-3d.png').is_file()
