import unittest
from provider_ledger import DDL, upsert_verified

class FakeCursor:
    def __init__(self, previous=None):
        self.previous = previous
        self.statements = []
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, args=None):
        self.statements.append((sql, args))
    def fetchone(self): return self.previous

class FakeConnection:
    def __init__(self, previous=None):
        self.cursor_obj = FakeCursor(previous)
    def cursor(self): return self.cursor_obj

def row(status="confirmed"):
    return dict(source_partner="amazon",source_account="account",external_id="order",
                source_report="report",source_sha256="a"*64,status=status,
                sale_amount_brl="100.00",commission_brl="10.00")

class LedgerTests(unittest.TestCase):
    def test_schema_has_composite_identity_and_audit(self):
        self.assertIn("PRIMARY KEY(source_partner, source_account, external_id)", DDL)
        self.assertIn("affiliate_conversion_audit", DDL)

    def test_insert_and_audit(self):
        conn = FakeConnection()
        self.assertEqual(upsert_verified(conn, row()), "inserted")
        self.assertTrue(any("INSERT INTO affiliate_conversion_audit" in q for q, _ in conn.cursor_obj.statements))

    def test_repeat_is_idempotent(self):
        old = tuple(row()[k] for k in ("source_partner","source_account","external_id",
                                      "source_report","source_sha256","status",
                                      "sale_amount_brl","commission_brl"))
        conn = FakeConnection(old)
        self.assertEqual(upsert_verified(conn, row()), "unchanged")
        self.assertFalse(any("INSERT INTO affiliate_conversion_audit" in q for q, _ in conn.cursor_obj.statements))

    def test_reversal_removes_confirmed_state(self):
        old = tuple(row()[k] for k in ("source_partner","source_account","external_id",
                                      "source_report","source_sha256","status",
                                      "sale_amount_brl","commission_brl"))
        conn = FakeConnection(old)
        self.assertEqual(upsert_verified(conn, row("reversed")), "updated")
        self.assertTrue(any("UPDATE affiliate_conversion_ledger" in q for q, _ in conn.cursor_obj.statements))

    def test_reject_unapproved_partner_and_invalid_sha_before_sql(self):
        invalid = (
            {"source_partner": "unknown"},
            {"source_sha256": "z" * 64},
            {"source_sha256": "A" * 64},
            {"source_sha256": "a" * 63},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                conn = FakeConnection()
                with self.assertRaises(ValueError):
                    upsert_verified(conn, {**row(), **changes})
                self.assertEqual(conn.cursor_obj.statements, [])

    def test_reject_invalid_input_without_sql(self):
        conn = FakeConnection()
        with self.assertRaises(ValueError):
            upsert_verified(conn, {**row(), "commission_brl": "-1"})
        self.assertEqual(conn.cursor_obj.statements, [])
