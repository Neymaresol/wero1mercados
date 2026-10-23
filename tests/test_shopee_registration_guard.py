import ast
from pathlib import Path


def test_shopee_registration_guard_precedes_db_write():
    tree = ast.parse(Path("main.py").read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "register_commercial_offer")
    source = ast.get_source_segment(Path("main.py").read_text(encoding="utf-8"), function)
    assert source is not None
    assert "SHOPEE_RELEASE_BLOCKED" in source
    assert "evaluate_shopee_release(ShopeeReleaseEvidence())" in source
    assert source.index("SHOPEE_RELEASE_BLOCKED") < source.index("with db() as conn:")
