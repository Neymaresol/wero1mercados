"""Regression tests for the fail-closed affiliate conversion provenance gate.

These tests do not call HTTP endpoints, touch a database, create clicks,
or generate sales. They only verify that unverified input is rejected.
"""
import ast
import unittest
from pathlib import Path

from p0_conversion_gate import reject_unverified_manual_conversion, verified_rows
from provider_reconciliation import Provenance


ROOT = Path(__file__).resolve().parents[1]


class ConversionGateTests(unittest.TestCase):
    def test_manual_conversion_gate_rejects_every_unverified_call(self):
        with self.assertRaisesRegex(
            PermissionError,
            "manual conversion is not authenticated partner evidence",
        ):
            reject_unverified_manual_conversion()

    def test_verified_rows_rejects_unverified_partner_provenance_before_parsing(self):
        provenance = Provenance(
            partner="amazon",
            account_id="test-account",
            report_id="test-report",
            sha256="0" * 64,
            verified=False,
        )
        with self.assertRaisesRegex(ValueError, "authenticated partner provenance required"):
            verified_rows(partner="amazon", raw=b"", provenance=provenance, columns={})

    def test_verified_rows_rejects_partner_identity_mismatch(self):
        provenance = Provenance(
            partner="amazon",
            account_id="test-account",
            report_id="test-report",
            sha256="0" * 64,
            verified=True,
        )
        with self.assertRaisesRegex(ValueError, "partner identity mismatch"):
            verified_rows(partner="shopee", raw=b"", provenance=provenance, columns={})

    def test_provider_conversion_endpoint_calls_fail_closed_gate(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        endpoint = next(
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "ingest_provider_conversion"
        )
        body = ast.get_source_segment(source, endpoint)
        self.assertIn("reject_unverified_manual_conversion()", body)
        self.assertIn("raise HTTPException(status_code=403", body)


if __name__ == "__main__":
    unittest.main()
