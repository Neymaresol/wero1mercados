"""Static P0 route contracts; does not import app or touch production data.

These checks are intentionally *not* HTTP/integration tests. They catch
accidental route-method and guard removals while the staging DB isolation
and full Double Check remain pending.
"""
import ast
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTIONS = {node.name: node for node in TREE.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def routes(function_name):
    found = set()
    for decorator in FUNCTIONS[function_name].decorator_list:
        if (isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "app"
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)):
            found.add((decorator.func.attr, decorator.args[0].value))
    return found


def body(function_name):
    return ast.get_source_segment(SOURCE, FUNCTIONS[function_name])


class P0RouteContractTests(unittest.TestCase):
    def test_go_is_get_landing_with_authorized_destination(self):
        self.assertIn(("get", "/go/{offer_id}"), routes("go_offer_landing"))
        code = body("go_offer_landing")
        self.assertIn("validate_authorized_url(", code)
        self.assertIn("require_affiliate_attribution(", code)
        self.assertIn("INSERT INTO offer_landing_visits", code)
        self.assertIn('action="/out/{offer_id}', code)

    def test_out_requires_post_and_records_real_click(self):
        self.assertIn(("post", "/out/{offer_id}"), routes("confirm_offer_click"))
        self.assertNotIn(("get", "/out/{offer_id}"), routes("confirm_offer_click"))
        code = body("confirm_offer_click")
        self.assertIn("validate_authorized_url(", code)
        self.assertIn("require_affiliate_attribution(", code)
        self.assertIn("INSERT INTO clicks", code)
        self.assertIn("RedirectResponse(target, status_code=303)", code)

    def test_legacy_conversion_ingest_fails_closed_before_write(self):
        code = body("ingest_provider_conversion")
        self.assertIn(("post", "/api/commercial/conversions/provider"), routes("ingest_provider_conversion"))
        gate = code.index("reject_unverified_manual_conversion()")
        write = code.index("INSERT INTO conversions")
        self.assertLess(gate, write)
        self.assertIn("raise HTTPException(status_code=403", code)

    def test_health_performs_database_query(self):
        self.assertIn(("get", "/health"), routes("health"))
        code = body("health")
        self.assertIn('cur.execute("SELECT 1")', code)
        self.assertIn('"database_ok": database_ok', code)


if __name__ == "__main__":
    unittest.main()
