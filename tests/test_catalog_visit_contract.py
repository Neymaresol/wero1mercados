"""Contract checks for catalog access telemetry without a live database."""
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1].joinpath("main.py").read_text()

class CatalogVisitContract(unittest.TestCase):
    def test_persistent_counter_and_no_personal_data(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS catalog_visits", SOURCE)
        self.assertIn("INSERT INTO catalog_visits DEFAULT VALUES", SOURCE)
        self.assertIn('catalog_visits = cur.fetchone()["c"]', SOURCE)
        self.assertIn('"catalog_visits": catalog_visits', SOURCE)
        self.assertIn("C.catalog_visits||0", SOURCE)
        self.assertNotIn("INSERT INTO catalog_visits (ip", SOURCE)

if __name__ == "__main__":
    unittest.main()
