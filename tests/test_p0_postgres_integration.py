"""Actual FastAPI + isolated PostgreSQL route tests; never target production."""
import os
import unittest

class FunnelPostgresIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("P0_TEST_DATABASE_URL")
        if not cls.url or "localhost" not in cls.url and "127.0.0.1" not in cls.url:
            raise unittest.SkipTest("Isolated localhost P0_TEST_DATABASE_URL required")
        import psycopg
        from fastapi.testclient import TestClient
        cls.psycopg = psycopg
        cls.TestClient = TestClient
        import main
        main.DATABASE_URL = cls.url
        cls.main = main
        cls.client = cls.TestClient(main.app)
        cls.client.__enter__()
        with cls.psycopg.connect(cls.url) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO partners(name,domain,active) VALUES('Test Amazon','amazon.com.br',TRUE) ON CONFLICT(domain) DO UPDATE SET active=TRUE RETURNING id")
                pid = cur.fetchone()[0]
                cur.execute("INSERT INTO offers(partner_id,title,authorized_url,active) VALUES(%s,%s,%s,TRUE) RETURNING id",(pid,"Isolated test offer","https://www.amazon.com.br/test",))
                cls.offer_id = cur.fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,"client"):
            cls.client.__exit__(None,None,None)

    def counts(self):
        with self.psycopg.connect(self.url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM offer_landing_visits WHERE offer_id=%s",(self.offer_id,))
                visits=cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM clicks WHERE offer_id=%s",(self.offer_id,))
                clicks=cur.fetchone()[0]
        return visits,clicks

    def test_landing_then_outbound(self):
        before=self.counts()
        landing=self.client.get(f"/go/{self.offer_id}?channel=test&campaign=p0")
        self.assertEqual(landing.status_code,200)
        self.assertEqual(self.counts(),(before[0]+1,before[1]))
        out=self.client.post(f"/out/{self.offer_id}?channel=test&campaign=p0",follow_redirects=False)
        self.assertEqual(out.status_code,303)
        self.assertEqual(out.headers["location"],"https://www.amazon.com.br/test")
        self.assertEqual(self.counts(),(before[0]+1,before[1]+1))

    def test_invalid_offer_no_click(self):
        before=self.counts()
        response=self.client.post("/out/999999999",follow_redirects=False)
        self.assertEqual(response.status_code,404)
        self.assertEqual(self.counts(),before)

    def test_legacy_conversion_fail_closed(self):
        # Even with an admin token, this endpoint must not manufacture partner sales.
        self.main.WERO_ADMIN_TOKEN = "isolated-token"
        r=self.client.post("/api/commercial/conversions/provider",headers={"Authorization":"Bearer isolated-token"},json={"external_id":"synthetic","offer_id":self.offer_id,"status":"confirmed","confirmed_at":"2026-10-13T10:00:00Z"})
        self.assertEqual(r.status_code,403)
        with self.psycopg.connect(self.url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM conversions WHERE external_id='synthetic'")
                self.assertEqual(cur.fetchone()[0],0)


    def test_admin_funnel_audit_requires_auth_and_remains_read_only(self):
        previous_token = self.main.WERO_ADMIN_TOKEN
        try:
            self.main.WERO_ADMIN_TOKEN = "isolated-audit-token"
            before = self.counts()
            unauthorized = self.client.get("/api/p0/funnel-audit")
            self.assertEqual(unauthorized.status_code, 401)
            authorized = self.client.get(
                "/api/p0/funnel-audit",
                headers={"Authorization": "Bearer isolated-audit-token"},
            )
            self.assertEqual(authorized.status_code, 200)
            body = authorized.json()
            self.assertEqual(body["source"], "application_database_connection")
            self.assertEqual([item["id"] for item in body["offers"]], [164, 802])
            self.assertEqual(body["financial_provenance"], "partner_report_not_authenticated_by_this_audit")
            self.assertNotIn("'authorized_url':", str(body))
            self.assertNotIn("postgresql://", str(body))
            self.assertEqual(self.counts(), before)
        finally:
            self.main.WERO_ADMIN_TOKEN = previous_token

if __name__=="__main__":
    unittest.main()
