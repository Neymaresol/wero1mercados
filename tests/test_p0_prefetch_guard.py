"""Pure regression tests for the explicit prefetch/prerender visit guard.

These tests exercise only header classification. They make no HTTP requests,
do not touch PostgreSQL, and do not create visits, clicks, conversions or sales.
"""
from p0_prefetch_guard import should_count_landing_visit


def test_declared_prefetch_and_prerender_headers_are_excluded():
    assert should_count_landing_visit({"purpose": "prefetch"}) is False
    assert should_count_landing_visit({"sec-purpose": "prerender"}) is False
    assert should_count_landing_visit({"x-moz": "prefetch"}) is False


def test_prefetch_header_matching_is_case_insensitive():
    assert should_count_landing_visit({"purpose": "PrEfEtCh"}) is False
    assert should_count_landing_visit({"sec-purpose": "PrErEnDeR"}) is False


def test_ordinary_navigation_headers_remain_consultative_only():
    assert should_count_landing_visit({"purpose": "navigate"}) is True
    assert should_count_landing_visit({}) is True
