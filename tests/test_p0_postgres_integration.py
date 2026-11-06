"""Actual FastAPI + isolated PostgreSQL route tests; never target production."""
import os
import re
import ast
import copy
import unittest
from unittest import mock

from p0_outbound_action import digest_action_token


class FunnelPostgresIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("P0_TEST_DATABASE_URL")
        if not cls.url or ("localhost" not in cls.url and "127.0.0.1" not in cls.url):
            raise unittest.SkipTest("Isolated localhost P0_TEST_DATABASE_URL required")
        import psycopg
        from fastapi.testclient import TestClient

        cls.psycopg = psycopg
        cls.TestClient = TestClient
        import main

        main.DATABASE_URL = cls.url
        cls.main = main
        # This suite is guarded to a disposable localhost PostgreSQL database.
        # Bootstrap its schema and fixtures explicitly; application startup is
        # intentionally read-only unless an operator opts into staging bootstrap.
        main.init_db()
        main.seed_amazon_campaigns()
        main.seed_additional_amazon_campaigns()
        cls.client = cls.TestClient(main.app)
        cls.client.__enter__()
        with cls.psycopg.connect(cls.url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO partners(name,domain,active) "
                    "VALUES('Test Amazon','amazon.com.br',TRUE) "
                    "ON CONFLICT(domain) DO UPDATE SET active=TRUE RETURNING id"
                )
                partner_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO offers(partner_id,title,authorized_url,active) "
                    "VALUES(%s,%s,%s,TRUE) RETURNING id",
                    (
                        partner_id,
                        "Isolated test offer",
                        "https://www.amazon.com.br/test?tag=isolated-ci-20",
                    ),
                )
                cls.offer_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO offers(partner_id,title,authorized_url,active) "
                    "VALUES(%s,%s,%s,TRUE) RETURNING id",
                    (
                        partner_id,
                        "Isolated second test offer",
                        "https://www.amazon.com.br/test-second?tag=isolated-ci-20",
                    ),
                )
                cls.other_offer_id = cur.fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "client"):
            cls.client.__exit__(None, None, None)

    def counts(self, offer_id=None):
        offer_id = self.offer_id if offer_id is None else offer_id
        with self.psycopg.connect(self.url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM offer_landing_visits WHERE offer_id=%s",
                    (offer_id,),
                )
                visits = cur.fetchone()[0]
                cur.execute(
                    "SELECT COUNT(*) FROM clicks WHERE offer_id=%s",
                    (offer_id,),
                )
                clicks = cur.fetchone()[0]
        return visits, clicks

    def action_token(self, response):
        self.assertEqual(response.status_code, 200)
        match = re.search(r'name="action_token" value="([^"]+)"', response.text)
        self.assertIsNotNone(match, "landing must issue one hidden action token")
        return match.group(1)

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
            self.assertEqual(
                body["financial_provenance"],
                "partner_report_not_authenticated_by_this_audit",
            )
            self.assertNotIn("'authorized_url':", str(body))
            self.assertNotIn("postgresql://", str(body))
            self.assertEqual(self.counts(), before)
        finally:
            self.main.WERO_ADMIN_TOKEN = previous_token

    def test_expired_action_token_is_rejected_without_click(self):
        token = "E" * 43
        token_hash = digest_action_token(token)
        with self.psycopg.connect(self.url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO outbound_action_tokens(
                        token_hash,offer_id,channel,campaign,created_at
                    )
                    VALUES(%s,%s,'test','expired',NOW() - INTERVAL '11 minutes')
                    """,
                    (token_hash, self.offer_id),
                )
        before = self.counts()
        response = self.client.post(
            f"/out/{self.offer_id}",
            data={"action_token": token},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.counts(), before)

    def test_invalid_offer_no_click(self):
        token = self.action_token(self.client.get(f"/go/{self.offer_id}"))
        after_landing = self.counts()
        response = self.client.post(
            "/out/999999999",
            data={"action_token": token},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.counts(), after_landing)

    def test_landing_then_outbound_and_replay_rejected(self):
        before = self.counts()
        landing = self.client.get(f"/go/{self.offer_id}?channel=test&campaign=p0")
        token = self.action_token(landing)
        self.assertEqual(landing.headers.get("cache-control"), "no-store, private")
        self.assertEqual(self.counts(), (before[0] + 1, before[1]))

        outbound = self.client.post(
            f"/out/{self.offer_id}",
            data={"action_token": token},
            follow_redirects=False,
        )
        self.assertEqual(outbound.status_code, 303)
        self.assertEqual(
            outbound.headers["location"],
            "https://www.amazon.com.br/test?tag=isolated-ci-20",
        )
        expected = (before[0] + 1, before[1] + 1)
        self.assertEqual(self.counts(), expected)

        replay = self.client.post(
            f"/out/{self.offer_id}",
            data={"action_token": token},
            follow_redirects=False,
        )
        self.assertEqual(replay.status_code, 403)
        self.assertEqual(self.counts(), expected)

    def test_legacy_amazon_get_redirects_without_recording_click(self):
        before = self.counts()
        response = self.client.get(
            f"/campanha/werozinha/amazon/{self.offer_id}",
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/go/{self.offer_id}?", response.headers["location"])
        self.assertEqual(self.counts(), before)

    def test_legacy_conversion_fail_closed(self):
        previous_token = self.main.WERO_ADMIN_TOKEN
        try:
            self.main.WERO_ADMIN_TOKEN = "isolated-token"
            response = self.client.post(
                "/api/commercial/conversions/provider",
                headers={"Authorization": "Bearer isolated-token"},
                json={
                    "external_id": "synthetic",
                    "offer_id": self.offer_id,
                    "status": "confirmed",
                    "confirmed_at": "2026-10-13T10:00:00Z",
                },
            )
            self.assertEqual(response.status_code, 403)
            with self.psycopg.connect(self.url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM conversions WHERE external_id='synthetic'"
                    )
                    self.assertEqual(cur.fetchone()[0], 0)
        finally:
            self.main.WERO_ADMIN_TOKEN = previous_token

    def test_token_is_bound_to_the_offer(self):
        token = self.action_token(self.client.get(f"/go/{self.offer_id}"))
        before_first = self.counts()
        before_second = self.counts(self.other_offer_id)
        response = self.client.post(
            f"/out/{self.other_offer_id}",
            data={"action_token": token},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.counts(), before_first)
        self.assertEqual(self.counts(self.other_offer_id), before_second)


class StartupBootstrapGateTests(unittest.TestCase):
    def test_startup_mutations_require_explicit_staging_opt_in(self):
        # Execute only the two pure startup-gate functions from main.py's AST.
        # This keeps the offline safety workflow independent of FastAPI/psycopg
        # and guarantees no database connection or write can occur here.
        from pathlib import Path

        source_path = Path(__file__).resolve().parents[1] / "main.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name in {"startup_bootstrap_enabled", "startup"}
        }
        self.assertEqual(set(functions), {"startup_bootstrap_enabled", "startup"})

        startup_node = copy.deepcopy(functions["startup"])
        startup_node.decorator_list = []
        module = ast.Module(
            body=[
                copy.deepcopy(functions["startup_bootstrap_enabled"]),
                startup_node,
            ],
            type_ignores=[],
        )
        ast.fix_missing_locations(module)

        init_db = mock.Mock()
        seed_amazon = mock.Mock()
        seed_additional = mock.Mock()
        namespace = {
            "os": os,
            "WERO_MODE": "production",
            "init_db": init_db,
            "seed_amazon_campaigns": seed_amazon,
            "seed_additional_amazon_campaigns": seed_additional,
        }
        exec(compile(module, str(source_path), "exec"), namespace)

        env_names = ("WERO_DEPLOYMENT_ENV", "WERO_ALLOW_STARTUP_DB_MUTATIONS")
        previous_env = {name: os.environ.get(name) for name in env_names}
        try:
            # Production mode blocks bootstrap even if the staging opt-in is set.
            namespace["WERO_MODE"] = "production"
            os.environ["WERO_DEPLOYMENT_ENV"] = "staging"
            os.environ["WERO_ALLOW_STARTUP_DB_MUTATIONS"] = "1"
            namespace["startup"]()

            # A production deployment label blocks bootstrap too.
            namespace["WERO_MODE"] = "staging"
            os.environ["WERO_DEPLOYMENT_ENV"] = "production"
            namespace["startup"]()

            # Staging without explicit opt-in remains read-only.
            os.environ["WERO_DEPLOYMENT_ENV"] = "staging"
            os.environ.pop("WERO_ALLOW_STARTUP_DB_MUTATIONS", None)
            namespace["startup"]()

            init_db.assert_not_called()
            seed_amazon.assert_not_called()
            seed_additional.assert_not_called()

            # The positive predicate is checked without invoking startup.
            os.environ["WERO_ALLOW_STARTUP_DB_MUTATIONS"] = "yes"
            self.assertTrue(namespace["startup_bootstrap_enabled"]())
        finally:
            for name, value in previous_env.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

if __name__ == "__main__":
    unittest.main()
