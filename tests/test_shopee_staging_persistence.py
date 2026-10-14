import unittest
from integrations.shopee_staging_persistence import persist_shopee_batch

class FakeCursor:
    def __init__(self):
        self.calls = []
        self.last = []
    def execute(self, sql, params):
        self.calls.append((sql, params))
        if "SELECT authorized_url" in sql:
            self.last = [("https://s.shopee.com.br/existing",)]
        elif "SELECT id, active FROM partners" in sql:
            self.last = [(7, False)]
        elif "RETURNING id" in sql:
            self.last = [(116,)]
    def fetchall(self):
        return self.last
    def fetchone(self):
        return self.last[0] if self.last else None
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False

class FakeConnection:
    def __init__(self):
        self.cur = FakeCursor()
    def cursor(self):
        return self.cur

class StagingPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.connection = FakeConnection()
        self.rows = [{"title":"ALSONEW", "affiliate_url":"https://s.shopee.com.br/20wE9HOs46"}]
    def test_production_write_denied(self):
        with self.assertRaises(ValueError):
            persist_shopee_batch(self.connection,self.rows,environment="production",dry_run=False)
        self.assertFalse(self.connection.cur.calls)
    def test_dry_run_no_insert(self):
        result=persist_shopee_batch(self.connection,self.rows,environment="staging")
        self.assertEqual(result["inserted"],0)
        self.assertFalse(any("INSERT" in q for q,_ in self.connection.cur.calls))
    def test_staging_insert_inactive(self):
        result=persist_shopee_batch(self.connection,self.rows,environment="staging",dry_run=False)
        self.assertEqual(result["inserted"],1)
        inserts=[q for q,_ in self.connection.cur.calls if "INSERT INTO offers" in q]
        self.assertEqual(len(inserts),1)
        self.assertIn("FALSE,NULL,NULL,NULL",inserts[0])
    def test_duplicate_skipped(self):
        rows=[{"title":"Existing","affiliate_url":"https://s.shopee.com.br/existing"}]
        result=persist_shopee_batch(self.connection,rows,environment="staging",dry_run=False)
        self.assertEqual(result["inserted"],0)
