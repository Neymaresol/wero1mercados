"""Readiness regression: no production DB, outbound routes, or financial writes."""
import json
import unittest
from unittest.mock import patch

import main


class ReadinessProbeTests(unittest.TestCase):
    def test_database_unavailable_returns_http_503(self):
        with patch.object(main, "db", side_effect=RuntimeError("db unavailable")):
            response = main.ready()
        self.assertEqual(response.status_code, 503)
        payload = json.loads(response.body)
        self.assertEqual(payload["status"], "degraded")
        self.assertIs(payload["database_ok"], False)
        self.assertIs(payload["storage_persistent"], False)
        self.assertNotIn("DATABASE_URL", response.body.decode())

    def test_successful_db_select_returns_http_200(self):
        with patch.object(main, "health", return_value={
            "status": "ok", "database_ok": True, "storage_persistent": True
        }):
            response = main.ready()
        self.assertEqual(response.status_code, 200)
        self.assertIs(json.loads(response.body)["database_ok"], True)

    def test_degraded_status_never_returns_http_200(self):
        with patch.object(main, "health", return_value={
            "status": "degraded", "database_ok": True, "storage_persistent": False
        }):
            response = main.ready()
        self.assertEqual(response.status_code, 503)

    def test_false_storage_persistence_never_returns_http_200(self):
        with patch.object(main, "health", return_value={
            "status": "ok", "database_ok": True, "storage_persistent": False
        }):
            response = main.ready()
        self.assertEqual(response.status_code, 503)

    def test_false_database_ok_never_returns_http_200(self):
        with patch.object(main, "health", return_value={
            "status": "ok", "database_ok": False, "storage_persistent": False
        }):
            response = main.ready()
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
