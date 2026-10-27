"""Offline traffic-quality regression; never invokes routes or writes events."""
import ast
from pathlib import Path
import unittest

from p0_prefetch_guard import should_count_landing_visit


class PrefetchGuardTests(unittest.TestCase):
    def test_declared_prefetch_does_not_count(self):
        for headers in (
            {"purpose": "prefetch"},
            {"Sec-Purpose": "prefetch;prerender"},
            {"x-moz": "prefetch"},
            {"purpose": "PrErEnDeR"},
        ):
            with self.subTest(headers=headers):
                self.assertFalse(should_count_landing_visit(
                    {k.lower(): v for k, v in headers.items()}
                ))

    def test_regular_get_remains_unverified_not_authenticated(self):
        self.assertTrue(should_count_landing_visit({}))
        self.assertTrue(should_count_landing_visit({"purpose": "navigate"}))
        self.assertTrue(should_count_landing_visit({"user-agent": "bot"}))

    def test_landing_route_applies_guard_before_insert(self):
        source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "go_offer_landing")
        body = ast.get_source_segment(source, fn)
        self.assertIn("request: Request", body)
        self.assertIn("should_count_landing_visit(request.headers)", body)
        self.assertIn("INSERT INTO offer_landing_visits", body)
        self.assertLess(body.index("should_count_landing_visit(request.headers)"),
                        body.index("INSERT INTO offer_landing_visits"))


if __name__ == "__main__":
    unittest.main()
