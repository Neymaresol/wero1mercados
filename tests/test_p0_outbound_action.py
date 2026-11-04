"""Offline tests for single-use /out action tokens; no DB or HTTP writes."""
import ast
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


def test_urlencoded_token_is_extracted_and_hashed_without_persisting_raw_value():
    token = "A" * 43
    body = urlencode({"action_token": token}).encode("ascii")
    assert extract_action_token("application/x-www-form-urlencoded", body) == token
    digest = digest_action_token(token)
    assert len(digest) == 64
    assert token not in digest


def test_token_parser_rejects_wrong_content_type_duplicate_and_oversized_body():
    token = "B" * 43
    with __import__("pytest").raises(ValueError):
        extract_action_token("application/json", b'{"action_token":"%s"}' % token.encode())
    with __import__("pytest").raises(ValueError):
        extract_action_token(
            "application/x-www-form-urlencoded",
            urlencode([("action_token", token), ("action_token", token)]).encode(),
        )
    with __import__("pytest").raises(ValueError):
        extract_action_token(
            "application/x-www-form-urlencoded",
            b"x" * 2049,
        )


def test_token_digest_rejects_short_or_non_url_safe_values():
    with __import__("pytest").raises(ValueError):
        digest_action_token("short")
    with __import__("pytest").raises(ValueError):
        digest_action_token("A" * 42 + "/")


def test_landing_issues_offer_bound_token_and_disables_caching():
    body = _function_source("go_offer_landing")
    assert "secrets.token_urlsafe(32)" in body
    assert "digest_action_token(action_token)" in body
    assert "INSERT INTO outbound_action_tokens" in body
    assert 'name="action_token"' in body
    assert 'response.headers["Cache-Control"] = "no-store, private"' in body
    assert "INSERT INTO clicks" not in body


def test_out_consumes_unexpired_token_once_before_inserting_click():
    body = _function_source("confirm_offer_click")
    assert "extract_action_token" in body
    assert "UPDATE outbound_action_tokens" in body
    assert "consumed_at IS NULL" in body
    assert "INTERVAL '10 minutes'" in body
    assert "RETURNING channel, campaign" in body
    assert body.index("UPDATE outbound_action_tokens") < body.index("INSERT INTO clicks")
    assert 'action["channel"]' in body
    assert 'action["campaign"]' in body
    assert "Query(" not in body


def test_token_table_stores_digest_and_supports_atomic_consumption():
    assert "CREATE TABLE IF NOT EXISTS outbound_action_tokens" in SOURCE
    assert "token_hash TEXT PRIMARY KEY" in SOURCE
    assert "consumed_at TIMESTAMPTZ" in SOURCE
