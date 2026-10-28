"""P0 offline contract: SELECT 1 is connectivity, not proof of durability.

These tests parse source and evaluate a pure readiness helper. They never
contact HTTP endpoints, connect to Postgres, or create commercial events.
"""
import ast
from pathlib import Path
import unittest

from p0_readiness import readiness_http_status

ROOT = Path(__file__).resolve().parents[1]


def health_fields():
    tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "health")
    report = next(n.value for n in ast.walk(fn)
                  if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict))
    return {k.value: v for k, v in zip(report.keys, report.values)
            if isinstance(k, ast.Constant) and isinstance(k.value, str)}


class HealthDurabilityContractTests(unittest.TestCase):
    def test_read_only_health_does_not_claim_verified_persistence(self):
        fields = health_fields()
        self.assertIsInstance(fields["storage_persistent"], ast.Constant)
        self.assertIsNone(fields["storage_persistent"].value)
        self.assertIs(fields["storage_persistence_verified"].value, False)
        self.assertEqual(fields["health_scope"].value, "database_connectivity_only")

    def test_readiness_fails_closed_when_durability_unverified(self):
        report = {"status": "ok", "database_ok": True,
                  "storage_persistent": None,
                  "storage_persistence_verified": False}
        self.assertEqual(readiness_http_status(report), 503)
        self.assertEqual(readiness_http_status({
            **report, "storage_persistent": False
        }), 503)

    def test_existing_explicitly_verified_readiness_contract_unchanged(self):
        self.assertEqual(readiness_http_status({
            "status": "ok", "database_ok": True, "storage_persistent": True
        }), 200)


if __name__ == "__main__":
    unittest.main()
