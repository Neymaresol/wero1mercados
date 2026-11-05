"""Offline tests for single-use /out action tokens; no DB or HTTP writes."""
import ast
import unittest
from pathlib import Path
from urllib.parse import urlencode

from p0_outbound_action import digest_action_token, extract_action_token

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")


def _function_source(name):
    tree = ast.parse(SOURCE)
    node = next(
        item for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == name
    )
    return ast.get_source_segment(SOURCE, node)


class OutboundActionTokenTests(unittest.TestCase):
    def test_urlencoded_token_is_extracted_and_hashed_without_persisting_raw_value(self):
        token = "A" * 43
        body = urlencode({"action_token": token}).encode("ascii")
        self.assertEqual(extract_action_token("application/x-www-form-urlencoded", body), token)
        digest = digest_action_token(token)
        self.assertEqual(len(digest), 64)
        self.assertNotIn(token, digest)

    def test_token_parser_rejects_wrong_content_type_duplicate_and_oversized_body(self):
        token = "B" * 43
        with self.assertRaises(ValueError):
            extract_action_token("application/json", b'{"action_token":"%s"}' % token.encode())
        with self.assertRaises(ValueError):
            extract_action_token(
                "application/x-www-form-urlencoded",
                urlencode([("action_token", token), ("action_token", token)]).encode(),
            )
        with self.assertRaises(ValueError):
            extract_action_token("application/x-www-form-urlencoded", b"x" * 2049)

    def test_token_digest_rejects_short_or_non_url_safe_values(self):
        with self.assertRaises(ValueError):
            digest_action_token("short")
        with self.assertRaises(ValueError):
            digest_action_token("A" * 42 + "/")

    def test_landing_issues_offer_bound_token_and_disables_caching(self):
        body = _function_source("go_offer_landing")
        self.assertIn("secrets.token_urlsafe(32)", body)
        self.assertIn("digest_action_token(action_token)", body)
        self.assertIn("INSERT INTO outbound_action_tokens", body)
        self.assertIn('name="action_token"', body)
        self.assertIn('response.headers["Cache-Control"] = "no-store, private"', body)
        self.assertNotIn("INSERT INTO clicks", body)

    def test_out_consumes_unexpired_token_once_before_inserting_click(self):
        body = _function_source("confirm_offer_click")
        self.assertIn("extract_action_token", body)
        self.assertIn("async for chunk in request.stream()", body)
        self.assertIn("MAX_BODY_BYTES", body)
        self.assertIn("UPDATE outbound_action_tokens", body)
        self.assertIn("consumed_at IS NULL", body)
        self.assertIn("INTERVAL '10 minutes'", body)
        self.assertIn("RETURNING channel, campaign", body)
        self.assertLess(body.index("UPDATE outbound_action_tokens"), body.index("INSERT INTO clicks"))
        self.assertIn('action["channel"]', body)
        self.assertIn('action["campaign"]', body)
        self.assertNotIn("Query(", body)

    def test_token_table_stores_digest_and_supports_atomic_consumption(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS outbound_action_tokens", SOURCE)
        self.assertIn("token_hash TEXT PRIMARY KEY", SOURCE)
        self.assertIn("consumed_at TIMESTAMPTZ", SOURCE)

    def test_startup_database_writes_require_explicit_staging_opt_in(self):
        guard = _function_source("startup_bootstrap_enabled")
        startup_body = _function_source("startup")
        self.assertIn('os.getenv("WERO_DEPLOYMENT_ENV"', guard)
        self.assertIn('os.getenv("WERO_ALLOW_STARTUP_DB_MUTATIONS"', guard)
        self.assertIn('deployment_env == "staging"', guard)
        self.assertIn('explicit_opt_in in {"1", "true", "yes"}', guard)
        self.assertIn('WERO_MODE != "production"', guard)
        self.assertIn("if not startup_bootstrap_enabled():", startup_body)
        self.assertLess(
            startup_body.index("if not startup_bootstrap_enabled():"),
            startup_body.index("init_db()"),
        )


if __name__ == "__main__":
    unittest.main()
