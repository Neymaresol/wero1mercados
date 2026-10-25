"""Offline database identity preflight tests: no credentials or network."""
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "ops" / "p0_db_identity_preflight.py"
SPEC = importlib.util.spec_from_file_location("p0_db_identity_preflight", FILE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DatabaseIdentityPreflightTests(unittest.TestCase):
    def test_correct_database_and_tables(self):
        self.assertEqual(MODULE.evaluate(("wero1mercados", True, True, True, True),
                                         "wero1mercados")["status"], "pass")

    def test_wrong_database_fails_closed(self):
        result = MODULE.evaluate(("neondb", True, True, True, True), "wero1mercados")
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["database_name_match"])

    def test_missing_table_fails_closed(self):
        result = MODULE.evaluate(("wero1mercados", True, True, False, True), "wero1mercados")
        self.assertEqual(result["missing_tables"], ["conversions"])
        self.assertEqual(result["status"], "blocked")

    def test_missing_or_malformed_data_fails_closed(self):
        for row, expected in ((None, "wero1mercados"), ((), "wero1mercados"),
                              (("wero1mercados", 1, True, True, True), "wero1mercados"),
                              (("wero1mercados", True, True, True, True), "")):
            with self.subTest(row=row, expected=expected):
                self.assertEqual(MODULE.evaluate(row, expected)["status"], "blocked")

    def test_query_contains_only_read_only_select(self):
        self.assertTrue(MODULE.QUERY.startswith("SELECT current_database()"))
        for table in MODULE.REQUIRED_TABLES:
            self.assertIn("to_regclass('public." + table + "')", MODULE.QUERY)
        for unsafe in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER "):
            self.assertNotIn(unsafe, MODULE.QUERY)


if __name__ == "__main__":
    unittest.main()
