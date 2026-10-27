"""P0 offline regression for the legacy conversion boundary.

Never sends HTTP requests, touches a database, or creates conversion events.
Only verifies that the proposed staging code fails closed for manual reports.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def function_source(path, function_name):
    source = (ROOT / path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    )
    return ast.get_source_segment(source, func), func, source


class ConversionBoundaryTests(unittest.TestCase):
    def test_manual_conversion_gate_always_rejects_unverified_reports(self):
        body, _, _ = function_source(
            "p0_conversion_gate.py", "reject_unverified_manual_conversion"
        )
        self.assertIn("raise PermissionError", body)
        self.assertNotIn("return True", body)

    def test_provider_endpoint_checks_provenance_before_database_access(self):
        body, fn, source = function_source("main.py", "ingest_provider_conversion")
        self.assertIn("reject_unverified_manual_conversion()", body)
        self.assertIn("status_code=403", body)
        self.assertIn("with db() as conn:", body)
        self.assertLess(
            body.index("reject_unverified_manual_conversion()"),
            body.index("with db() as conn:"),
        )
        decorators = [
            ast.get_source_segment(source, decorator)
            for decorator in fn.decorator_list
        ]
        self.assertTrue(any(
            'app.post("/api/commercial/conversions/provider")' in decorator
            for decorator in decorators
        ))
        self.assertIn("Depends(require_admin)", body)

    def test_unverified_outbound_click_is_not_a_confirmed_conversion(self):
        body, fn, source = function_source("main.py", "confirm_offer_click")
        decorators = [
            ast.get_source_segment(source, decorator)
            for decorator in fn.decorator_list
        ]
        self.assertTrue(any(
            'app.post("/out/{offer_id}")' in decorator
            for decorator in decorators
        ))
        self.assertIn("INSERT INTO clicks", body)
        self.assertNotIn("INSERT INTO conversions", body)
        self.assertNotIn("UPDATE conversions", body)


if __name__ == "__main__":
    unittest.main()
