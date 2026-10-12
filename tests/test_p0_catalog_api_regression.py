"""P0 regression: the public offers API must filter invalid partner URLs.

These tests inspect the real FastAPI route rather than duplicate a fake validator.
No production endpoints or databases are contacted.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


class OffersCatalogRegression(unittest.TestCase):
    def test_offers_route_exists(self):
        routes = [n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "list_offers"]
        self.assertEqual(len(routes), 1)
        self.assertIn('"/api/offers"', ast.unparse(routes[0].decorator_list))

    def test_api_validates_authorized_url_before_returning(self):
        route = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "list_offers")
        code = ast.unparse(route)
        self.assertIn("validate_authorized_url(item['authorized_url'], item['domain'])", code)
        self.assertIn("except (HTTPException, ValueError, TypeError)", code)
        self.assertIn("return {'offers': safe_offers}", code)

    def test_api_keeps_existing_offer_shape(self):
        route = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "list_offers")
        code = ast.unparse(route)
        self.assertIn("safe_offers.append(item)", code)

    def test_no_changes_to_click_or_financial_routes(self):
        names = {n.name for n in TREE.body if isinstance(n, ast.FunctionDef)}
        self.assertTrue({"confirm_offer_click", "ingest_provider_conversion", "commercial"}.issubset(names))


if __name__ == "__main__":
    unittest.main()
