"""Offline affiliate funnel contract checks; no synthetic click or sale."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "main.py"

class AffiliateContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_public_routes(self):
        for route in ("/health", "/api/offers", "/api/acquisition", "/api/commercial"):
            with self.subTest(route=route):
                self.assertIn(repr(route), self.source)

    def test_click_and_conversion_routes_separated(self):
        self.assertIn('"/go/{offer_id}"', self.source)
        self.assertIn('"/out/{offer_id}"', self.source)
        self.assertIn('"/api/commercial/conversions/provider"', self.source)

    def test_source_is_valid_python(self):
        self.assertIsInstance(self.tree, ast.Module)

if __name__ == "__main__":
    unittest.main()
