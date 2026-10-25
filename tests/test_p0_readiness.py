"""Offline readiness tests: no app import, DB connection, routes, or writes."""
import ast
from pathlib import Path
import unittest

from p0_readiness import (
    readiness_http_status,
    database_identity_verified,
)


class ReadinessProbeTests(unittest.TestCase):
    def test_unavailable_database_is_503(self):
        self.assertEqual(readiness_http_status({
            "status": "degraded", "database_ok": False,
            "storage_persistent": False,
        }, True), 503)

    def test_healthy_database_requires_verified_identity(self):
        report = {"status": "ok", "database_ok": True, "storage_persistent": True}
        self.assertEqual(readiness_http_status(report), 503)
        self.assertEqual(readiness_http_status(report, False), 503)
        self.assertEqual(readiness_http_status(report, 1), 503)
        self.assertEqual(readiness_http_status(report, True), 200)

    def test_inconsistent_health_fails_closed(self):
        for report in (
            {"status": "degraded", "database_ok": True, "storage_persistent": True},
            {"status": "ok", "database_ok": False, "storage_persistent": True},
            {"status": "ok", "database_ok": True, "storage_persistent": False},
            {"status": "ok", "database_ok": 1, "storage_persistent": True},
            {}, None,
        ):
            with self.subTest(report=report):
                self.assertEqual(readiness_http_status(report, True), 503)

    def test_database_identity_requires_exact_name_and_all_tables(self):
        row = {"database_name": "wero1mercados", "offers": True, "clicks": True,
               "conversions": True, "offer_landing_visits": True}
        self.assertTrue(database_identity_verified(row, "wero1mercados"))
        self.assertFalse(database_identity_verified(row, "neondb"))
        self.assertFalse(database_identity_verified(row, ""))
        self.assertFalse(database_identity_verified(None, "wero1mercados"))
        self.assertFalse(database_identity_verified({**row, "conversions": 1}, "wero1mercados"))
        self.assertFalse(database_identity_verified({**row, "clicks": False}, "wero1mercados"))
        self.assertFalse(database_identity_verified({k: v for k, v in row.items()
                                                     if k != "offers"}, "wero1mercados"))

    def test_route_uses_same_db_and_does_not_write(self):
        source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "ready")
        route = ast.get_source_segment(source, fn)
        self.assertIn('@app.get("/ready", include_in_schema=False)', source)
        self.assertIn("report = health()", route)
        self.assertIn("EXPECTED_DATABASE_NAME", route)
        self.assertIn("with db() as conn", route)
        self.assertIn("current_database()", route)
        self.assertIn("database_identity_verified(cur.fetchone(), expected_name)", route)
        self.assertIn("readiness_http_status(report, identity_ok)", route)
        self.assertIn("JSONResponse(", route)
        self.assertNotIn("INSERT INTO", route)
        self.assertNotIn("UPDATE ", route)
        self.assertNotIn("DELETE FROM", route)


if __name__ == "__main__":
    unittest.main()
