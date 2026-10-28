"""Offline readiness tests: no app import, DB connection, routes, or writes."""
import ast
from pathlib import Path
import unittest

from p0_readiness import readiness_http_status


class ReadinessProbeTests(unittest.TestCase):
    def test_unavailable_database_is_503(self):
        self.assertEqual(readiness_http_status({
            "status": "degraded", "database_ok": False,
            "storage_persistent": False,
        }), 503)

    def test_verified_database_and_durability_is_200(self):
        self.assertEqual(readiness_http_status({
            "status": "ok", "database_ok": True,
            "storage_persistent": True,
            "storage_persistence_verified": True,
        }), 200)

    def test_inconsistent_health_fails_closed(self):
        for report in (
            {"status": "degraded", "database_ok": True, "storage_persistent": True, "storage_persistence_verified": True},
            {"status": "ok", "database_ok": False, "storage_persistent": True, "storage_persistence_verified": True},
            {"status": "ok", "database_ok": True, "storage_persistent": False, "storage_persistence_verified": True},
            {"status": "ok", "database_ok": 1, "storage_persistent": True, "storage_persistence_verified": True},
            {"status": "ok", "database_ok": True, "storage_persistent": True},
            {"status": "ok", "database_ok": True, "storage_persistent": True, "storage_persistence_verified": False},
            {}, None,
        ):
            with self.subTest(report=report):
                self.assertEqual(readiness_http_status(report), 503)

    def test_route_reuses_db_health_and_returns_actual_http_status(self):
        source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "ready")
        route = ast.get_source_segment(source, fn)
        self.assertIn('@app.get("/ready", include_in_schema=False)', source)
        self.assertIn("report = health()", route)
        self.assertIn("readiness_http_status(report)", route)
        self.assertIn("JSONResponse(status_code=", route)
        self.assertNotIn("INSERT INTO", route)
        self.assertNotIn("UPDATE ", route)


if __name__ == "__main__":
    unittest.main()
