"""Regression checks for fail-closed Amazon links across commercial paths."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def function(name):
    return next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == name)


class AmazonAllPathsTests(unittest.TestCase):
    def test_routes_gate_before_tracking_or_rendering(self):
        for name in ("go_offer_landing", "confirm_offer_click", "werozinha_amazon_campaign"):
            with self.subTest(name=name):
                node = function(name)
                calls = [
                    (n.func.id, n.lineno)
                    for n in ast.walk(node)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == "require_affiliate_attribution"
                ]
                self.assertTrue(calls, f"{name} missing attribution gate")
                self.assertIn("validate_authorized_url", ast.get_source_segment(SOURCE, node))

    def test_gate_only_targets_amazon(self):
        node = function("require_affiliate_attribution")
        source = ast.get_source_segment(SOURCE, node)
        self.assertIn('domain == "amazon.com.br"', source)
        self.assertIn("amazon_affiliate_tag", source)
        self.assertIn("HTTPException", source)


if __name__ == "__main__":
    unittest.main()
