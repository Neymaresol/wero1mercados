"""Regression tests for prefetch suppression and single-use outbound actions."""
import ast
from hashlib import sha256
from pathlib import Path

import pytest

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


def test_prefetch_and_prerender_headers_do_not_create_landing_visits():
    assert should_count_landing_visit({"purpose": "prefetch"}) is False
    assert should_count_landing_visit({"sec-purpose": "prefetch;prerender"}) is False
    assert should_count_landing_visit({"x-moz": "prerender"}) is False
    assert should_count_landing_visit({"accept": "text/html"}) is True
    assert should_count_landing_visit({}) is True


def test_action_token_parser_accepts_one_bounded_urlencoded_token():
    token = "A" * 32
    body = ("action_token=" + token).encode("ascii")
    assert extract_action_token(
        "application/x-www-form-urlencoded; charset=UTF-8", body
    ) == token


@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        ("application/json", b'{"action_token":"' + b"A" * 32 + b'"}'),
        ("application/x-www-form-urlencoded", b"action_token=short"),
        (
            "application/x-www-form-urlencoded",
            b"action_token=" + b"A" * 32 + b"&action_token=" + b"B" * 32,
        ),
        ("application/x-www-form-urlencoded", b"action_token=" + b"A" * 2048),
    ],
)
def test_action_token_parser_rejects_unsupported_duplicate_invalid_or_oversized(
    content_type, body
):
    with pytest.raises(ValueError):
        extract_action_token(content_type, body)


def test_action_token_storage_uses_sha256_digest_not_raw_token():
    token = "B" * 48
    digest = digest_action_token(token)
    assert digest == sha256(token.encode("utf-8")).hexdigest()
    assert digest != token
    assert len(digest) == 64
    with pytest.raises(ValueError):
        digest_action_token("too-short")


def test_prefetch_guard_precedes_visit_and_token_writes_in_go_handler():
    body = _function_source("go_offer_landing")
    guard = body.index("should_count_landing_visit")
    visit_write = body.index("INSERT INTO offer_landing_visits")
    token_write = body.index("INSERT INTO outbound_action_tokens")
    early_return = body.index("return Response(")
    assert guard < early_return < visit_write
    assert guard < token_write


def test_out_handler_atomically_consumes_offer_bound_unexpired_token_before_click():
    body = _function_source("confirm_offer_click")
    consume = body.index("UPDATE outbound_action_tokens")
    click_insert = body.index("INSERT INTO clicks")
    assert "extract_action_token" in body
    assert "digest_action_token" in body
    assert "token_hash=%s" in body
    assert "offer_id=%s" in body
    assert "consumed_at IS NULL" in body
    assert "created_at >= NOW() - INTERVAL '10 minutes'" in body
    assert "RETURNING channel, campaign" in body
    assert "if not action" in body
    assert consume < click_insert
