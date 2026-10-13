"""P0 offline Double Check: no production HTTP requests or fake clicks."""
import importlib.util
import pathlib
import unittest
from unittest.mock import Mock
from provider_reconciliation import Provenance, official_adapter, reconcile
import hashlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("identity", ROOT / "scripts" / "p0_database_identity.py")
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)

class P0DoubleCheck(unittest.TestCase):
    def test_config_redacts_secret_and_endpoint(self):
        env = {"DATABASE_URL": "postgresql://private:supersecret@internal.example:5432/prod", "DB_DIAGNOSTIC_KEY": "x"*32}
        output = str(identity.diagnose(env))
        for forbidden in ("private", "supersecret", "internal.example", "prod"):
            self.assertNotIn(forbidden, output)
        self.assertEqual(len(identity.diagnose(env)["fingerprint"]), 16)

    def test_missing_key_does_not_disclose_identity(self):
        self.assertIsNone(identity.diagnose({"DATABASE_URL":"postgresql://u:p@host/db"})["fingerprint"])

    def test_invalid_url_is_rejected(self):
        self.assertFalse(identity.diagnose({"DATABASE_URL":"sqlite:///tmp/x"})["valid_format"])

    def test_go_out_route_contract(self):
        # Static route contract: GET landing is not the outbound click.
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        go = source.split('@app.get("/go/{offer_id}"')[1].split('@app.post("/out/{offer_id}"')[0]
        out = source.split('@app.post("/out/{offer_id}"')[1].split("class ProviderConversionIn")[0]
        self.assertIn("offer_landing_visits", go)
        self.assertNotIn("INSERT INTO clicks", go)
        self.assertIn("INSERT INTO clicks", out)
        self.assertIn("RedirectResponse(target, status_code=303)", out)
        self.assertIn("validate_authorized_url", out)

    def test_partner_report_requires_provenance(self):
        raw = b"id,status,sale,fee\\n1,confirmed,100.00,10.00\\n".replace(b"\\n", b"\n")
        columns = {"external_id":"id","status":"status","sale_amount_brl":"sale","commission_brl":"fee"}
        p = Provenance("amazon","acct","report",hashlib.sha256(raw).hexdigest(),False)
        with self.assertRaises(ValueError):
            official_adapter("amazon",raw,p,columns)
        good = Provenance("amazon","acct","report",hashlib.sha256(raw).hexdigest(),True)
        rows = official_adapter("amazon",raw,good,columns)
        self.assertEqual(rows[0]["commission_brl"],"10.00")
        self.assertEqual(reconcile(rows[0],rows[0]),rows[0])

if __name__ == "__main__":
    unittest.main()
