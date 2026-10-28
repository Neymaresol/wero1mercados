import hashlib
import unittest
from provider_reconciliation import Provenance, official_adapter, reconcile

COLUMNS = {"external_id": "id", "status": "state", "sale_amount_brl": "sale", "commission_brl": "fee"}
RAW = b"id,state,sale,fee\norder-1,confirmed,120.00,12.00\n"

def provenance(partner="amazon", verified=True, digest=None):
    return Provenance(partner, "account-1", "report-20261012", digest or hashlib.sha256(RAW).hexdigest(), verified)

class ReconciliationTests(unittest.TestCase):
    def test_all_three_adapters(self):
        for partner in ("amazon", "shopee", "mercado_livre"):
            with self.subTest(partner=partner):
                rows = official_adapter(partner, RAW, provenance(partner), COLUMNS)
                self.assertEqual(rows[0]["status"], "confirmed")
                self.assertEqual(rows[0]["commission_brl"], "12.00")

    def test_rejects_unverified_source(self):
        with self.assertRaises(ValueError):
            official_adapter("amazon", RAW, provenance(verified=False), COLUMNS)

    def test_rejects_truthy_non_boolean_verification(self):
        # Strings and integers are truthy in Python but not authentication.
        for flag in ("false", "true", 1, -1, None):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                official_adapter("amazon", RAW, provenance(verified=flag), COLUMNS)

    def test_rejects_invalid_provenance_fields(self):
        base = provenance()
        for changes in (
            {"account_id": None},
            {"report_id": 123},
            {"sha256": None},
            {"sha256": "z" * 64},
            {"sha256": "a" * 63},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                official_adapter("amazon", RAW, Provenance(
                    changes.get("partner", base.partner),
                    changes.get("account_id", base.account_id),
                    changes.get("report_id", base.report_id),
                    changes.get("sha256", base.sha256),
                    base.verified,
                ), COLUMNS)

    def test_rejects_modified_report(self):
        with self.assertRaises(ValueError):
            official_adapter("amazon", RAW + b"extra", provenance(), COLUMNS)

    def test_rejects_partner_mismatch(self):
        with self.assertRaises(ValueError):
            official_adapter("shopee", RAW, provenance(), COLUMNS)

    def test_rejects_duplicate_in_report(self):
        data = RAW + b"order-1,confirmed,120.00,12.00\n"
        with self.assertRaises(ValueError):
            official_adapter("amazon", data, provenance(digest=hashlib.sha256(data).hexdigest()), COLUMNS)

    def test_idempotent_same_state(self):
        item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
        self.assertEqual(reconcile(item, item), item)

    def test_terminal_not_revived(self):
        item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
        for terminal in ("reversed", "cancelled"):
            with self.subTest(status=terminal), self.assertRaises(ValueError):
                reconcile({**item, "status": terminal}, item)

    def test_confirmed_can_be_reversed(self):
        item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
        self.assertEqual(reconcile(item, {**item, "status": "reversed"})["status"], "reversed")

    def test_confirmed_cannot_regress_to_pending(self):
        item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
        with self.assertRaises(ValueError):
            reconcile(item, {**item, "status": "pending"})

    def test_rejects_same_status_changed_commission(self):
        item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
        with self.assertRaises(ValueError):
            reconcile(item, {**item, "commission_brl": "99.00"})
