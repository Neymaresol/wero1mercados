"""Actual FastAPI + isolated PostgreSQL route tests; never target production."""
import os
import re
import unittest
from unittest.mock import patch

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
        cls.main.WERO_OUTBOUND_SIGNING_SECRET = "ci-only-outbound-signing-secret-at-least-32-bytes"
        cls.client = cls.TestClient(main.app)
        # Permit schema bootstrap only inside this isolated localhost CI database.
        previous_bootstrap = os.environ.get("WERO_ENABLE_STARTUP_SCHEMA_BOOTSTRAP")
        os.environ["WERO_ENABLE_STARTUP_SCHEMA_BOOTSTRAP"] = "true"
        try:
            cls.client.__enter__()
        finally:
            if previous_bootstrap is None:
                os.environ.pop("WERO_ENABLE_STARTUP_SCHEMA_BOOTSTRAP", None)
            else:
                os.environ["WERO_ENABLE_STARTUP_SCHEMA_BOOTSTRAP"] = previous_bootstrap
        with cls.psycopg.connect(cls.url) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO partners(name,domain,active) VALUES('Test Amazon','amazon.com.br',TRUE) ON CONFLICT(domain) DO UPDATE SET active=TRUE RETURNING id")
                pid = cur.fetchone()[0]
                cur.execute("INSERT INTO offers(partner_id,title,authorized_url,active) VALUES(%s,%s,%s,TRUE) RETURNING id",(pid,"Isolated test offer","https://www.amazon.com.br/test?tag=isolated-ci-20",))
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
                cur.execute("SELECT COUNT(*) FROM outbound_action_tokens WHERE offer_id=%s",(self.offer_id,))
                tokens=cur.fetchone()[0]
        return visits,clicks,tokens

    def test_landing_then_outbound_is_one_time_and_prefetch_safe(self):
        before=self.counts()
        landing=self.client.get(f"/go/{self.offer_id}?channel=test&campaign=p0")
        self.assertEqual(landing.status_code,200)
        # GET can be prefetched; it must not create a visit, token row, or click.
        self.assertEqual(self.counts(),before)
        match=re.search(r'name="outbound_token" value="([^"]+)"',landing.text)
        self.assertIsNotNone(match)
        token=match.group(1)
        out=self.client.post(
            f"/out/{self.offer_id}?channel=test&campaign=p0",
            data={"outbound_token":token},
            follow_redirects=False,
        )
        self.assertEqual(out.status_code,303)
        self.assertEqual(out.headers["location"],"https://www.amazon.com.br/test?tag=isolated-ci-20")
        after=self.counts()
        self.assertEqual(after,(before[0],before[1]+1,before[2]+1))
        replay=self.client.post(
            f"/out/{self.offer_id}?channel=test&campaign=p0",
            data={"outbound_token":token},
            follow_redirects=False,
        )
        self.assertEqual(replay.status_code,409)
        self.assertEqual(self.counts(),after)

    def test_missing_or_campaign_mismatched_token_is_rejected(self):
        before=self.counts()
        missing=self.client.post(f"/out/{self.offer_id}?channel=test&campaign=p0",data={},follow_redirects=False)
        self.assertEqual(missing.status_code,403)
        landing=self.client.get(f"/go/{self.offer_id}?channel=test&campaign=p0")
        token=re.search(r'name="outbound_token" value="([^"]+)"',landing.text).group(1)
        mismatch=self.client.post(
            f"/out/{self.offer_id}?channel=test&campaign=other",
            data={"outbound_token":token},
            follow_redirects=False,
        )
        self.assertEqual(mismatch.status_code,403)
        self.assertEqual(self.counts(),before)

    def test_invalid_offer_no_click(self):
        before=self.counts()
        response=self.client.post("/out/999999999",data={"outbound_token":"invalid"},follow_redirects=False)
        self.assertEqual(response.status_code,404)
        self.assertEqual(self.counts(),before)

    def test_expired_token_is_rejected(self):
        from fastapi import HTTPException
        with patch("main.time.time", return_value=1000):
            token=self.main.issue_outbound_action_token(self.offer_id,"test","p0",ttl_seconds=300)
        with patch("main.time.time", return_value=1301):
            with self.assertRaises(HTTPException) as caught:
                self.main.verify_outbound_action_token(token,self.offer_id,"test","p0")
        self.assertEqual(caught.exception.status_code,403)

    def test_landing_fails_closed_without_signing_secret(self):
        previous=self.main.WERO_OUTBOUND_SIGNING_SECRET
        before=self.counts()
        try:
            self.main.WERO_OUTBOUND_SIGNING_SECRET=""
            response=self.client.get(f"/go/{self.offer_id}?channel=test&campaign=p0")
            self.assertEqual(response.status_code,503)
            self.assertEqual(self.counts(),before)
        finally:
            self.main.WERO_OUTBOUND_SIGNING_SECRET=previous

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
