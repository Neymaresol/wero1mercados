"""Offline, non-mutating route-contract regression checks for the affiliate funnel.

These checks parse source only. They NEVER call /go, /out, SQL, HTTP, or partners.
They do not replace integrated staging HTTP validation.
"""
import ast
from pathlib import Path
import unittest


SOURCE = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def function_source(name):
    node = next(
        n for n in TREE.body
        if isinstance(n, ast.FunctionDef) and n.name == name
    )
    return ast.get_source_segment(SOURCE, node)


class FunnelContractTests(unittest.TestCase):
    def test_route_methods_prevent_automatic_click_on_landing(self):
        self.assertIn('@app.get("/go/{offer_id}"', SOURCE)
        self.assertIn('@app.post("/out/{offer_id}")', SOURCE)
        go = function_source("go_offer_landing")
        out = function_source("confirm_offer_click")
        self.assertIn('<form method="post"', go)
        self.assertNotIn("INSERT INTO clicks", go)
        self.assertNotIn("RedirectResponse(", go)
        self.assertIn("INSERT INTO clicks", out)
        self.assertIn("RedirectResponse(target, status_code=303)", out)

    def test_landing_visit_prefetch_gate_and_nonfinancial_events(self):
        go = function_source("go_offer_landing")
        out = function_source("confirm_offer_click")
        self.assertIn("should_count_landing_visit(request.headers)", go)
        self.assertIn("INSERT INTO offer_landing_visits", go)
        for route in (go, out):
            self.assertNotIn("INSERT INTO conversions", route)
            self.assertNotIn("affiliate_conversion_ledger", route)

    def test_both_routes_validate_partner_and_normalize_untrusted_labels(self):
        for name in ("go_offer_landing", "confirm_offer_click"):
            with self.subTest(route=name):
                route = function_source(name)
                self.assertIn("validate_authorized_url(", route)
                self.assertIn("require_affiliate_attribution(", route)
                self.assertIn("classify_channel(channel)", route)
                self.assertIn("safe_campaign(campaign)", route)


if __name__ == "__main__":
    unittest.main()
