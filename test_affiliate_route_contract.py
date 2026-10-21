"""Read-only route contract audit; never invokes /go/ or /out/ endpoints."""
import ast
from pathlib import Path
import unittest

class CommercialRouteContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(Path(__file__).with_name("main.py").read_text(encoding="utf-8"))
        cls.routes = {}
        for node in ast.walk(cls.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.args:
                        if isinstance(dec.func.value, ast.Name) and dec.func.value.id == "app":
                            try:
                                path = ast.literal_eval(dec.args[0])
                            except (ValueError, TypeError):
                                continue
                            cls.routes[(dec.func.attr, path)] = node
    def test_health_is_get(self):
        self.assertIn(("get", "/health"), self.routes)
    def test_vitrine_is_get(self):
        self.assertIn(("get", "/vitrine"), self.routes)
    def test_go_is_landing_not_redirect_get(self):
        node = self.routes[("get", "/go/{offer_id}")]
        self.assertIn("offer_landing_visits", ast.get_source_segment(Path(__file__).with_name("main.py").read_text(), node))
    def test_out_is_post_only(self):
        self.assertIn(("post", "/out/{offer_id}"), self.routes)
        self.assertNotIn(("get", "/out/{offer_id}"), self.routes)
    def test_click_recorded_only_in_out(self):
        src=Path(__file__).with_name("main.py").read_text()
        go=ast.get_source_segment(src,self.routes[("get", "/go/{offer_id}")])
        out=ast.get_source_segment(src,self.routes[("post", "/out/{offer_id}")])
        self.assertNotIn("INSERT INTO clicks",go)
        self.assertIn("INSERT INTO clicks",out)
        self.assertIn("require_affiliate_attribution",out)
        self.assertIn("validate_authorized_url",out)

if __name__ == "__main__":
    unittest.main()
