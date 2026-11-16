"""Regression tests for prefetch suppression and single-use outbound actions."""
import ast
from hashlib import sha256
from pathlib import Path
import unittest

from p0_outbound_action import digest_action_token, extract_action_token
from p0_prefetch_guard import should_count_landing_visit


def _function_source(name: str) -> str:
    source = Path("main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        item for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == name
    )
    return ast.get_source_segment(source, node)


class OutboundActionContractTests(unittest.TestCase):
    def test_prefetch_and_prerender_headers_do_not_create_landing_visits(self):
        self.assertFalse(should_count_landing_visit({"purpose": "prefetch"}))
        self.assertFalse(should_count_landing_visit({"sec-purpose": "prefetch;prerender"}))
        self.assertFalse(should_count_landing_visit({"x-moz": "prerender"}))
        self.assertTrue(should_count_landing_visit({"accept": "text/html"}))
        self.assertTrue(should_count_landing_visit({}))

    def test_action_token_parser_accepts_one_bounded_urlencoded_token(self):
        token = "A" * 32
        body = ("action_token=" + token).encode("ascii")
        self.assertEqual(
            extract_action_token(
                "application/x-www-form-urlencoded; charset=UTF-8", body
            ),
            token,
        )

    def test_action_token_parser_rejects_unsupported_duplicate_invalid_or_oversized(self):
        cases = [
            ("application/json", b'{"action_token":"' + b"A" * 32 + b'"}'),
            ("application/x-www-form-urlencoded", b"action_token=short"),
            (
                "application/x-www-form-urlencoded",
                b"action_token=" + b"A" * 32 + b"&action_token=" + b"B" * 32,
            ),
            ("application/x-www-form-urlencoded", b"action_token=" + b"A" * 2048),
        ]
        for content_type, body in cases:
            with self.subTest(content_type=content_type, body_length=len(body)):
                with self.assertRaises(ValueError):
                    extract_action_token(content_type, body)

    def test_action_token_storage_uses_sha256_digest_not_raw_token(self):
        token = "B" * 48
        digest = digest_action_token(token)
        self.assertEqual(digest, sha256(token.encode("utf-8")).hexdigest())
        self.assertNotEqual(digest, token)
        self.assertEqual(len(digest), 64)
        with self.assertRaises(ValueError):
            digest_action_token("too-short")

    def test_prefetch_guard_precedes_visit_and_token_writes_in_go_handler(self):
        body = _function_source("go_offer_landing")
        guard = body.index("should_count_landing_visit")
        visit_write = body.index("INSERT INTO offer_landing_visits")
        token_write = body.index("INSERT INTO outbound_action_tokens")
        early_return = body.index("return Response(")
        self.assertLess(guard, early_return)
        self.assertLess(early_return, visit_write)
        self.assertLess(guard, token_write)

    def test_out_handler_atomically_consumes_offer_bound_unexpired_token_before_click(self):
        body = _function_source("confirm_offer_click")
        consume = body.index("UPDATE outbound_action_tokens")
        click_insert = body.index("INSERT INTO clicks")
        self.assertIn("extract_action_token", body)
        self.assertIn("digest_action_token", body)
        self.assertIn("token_hash=%s", body)
        self.assertIn("offer_id=%s", body)
        self.assertIn("consumed_at IS NULL", body)
        self.assertIn("created_at >= NOW() - INTERVAL '10 minutes'", body)
        self.assertIn("RETURNING channel, campaign", body)
        self.assertIn("if not action", body)
        self.assertLess(consume, click_insert)


if __name__ == "__main__":
    unittest.main()
