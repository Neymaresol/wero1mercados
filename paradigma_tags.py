"""PARADIGMA TAG engines: ephemeral intent and aggregate trend signals.

This module never records individual queries, identities or follower lists.
It only creates contextual tags from text supplied by an authorized integration.
"""
import re
import unicodedata
from collections import Counter

STOPWORDS = frozenset({"eu", "quero", "ver", "preco", "precos", "comprar", "um", "uma", "de", "da", "do", "com", "para", "o", "a", "os", "as", "no", "na", "me", "mostre"})
MAX_TERMS = 12
MAX_INPUT = 256


def normalize_terms(query: str) -> tuple[str, ...]:
    if not isinstance(query, str):
        return ()
    normalized = unicodedata.normalize("NFKD", query[:MAX_INPUT]).encode("ascii", "ignore").decode("ascii").lower()
    tokens = re.findall(r"[a-z0-9]+", normalized)
    return tuple(dict.fromkeys(t for t in tokens if len(t) > 1 and t not in STOPWORDS))[:MAX_TERMS]


def search_tag(query: str) -> dict:
    """TAG 01: contextual, short-lived search intent; no persistence."""
    terms = normalize_terms(query)
    return {"tag_type": "search_intent", "terms": list(terms), "eligible": bool(terms)}


def trend_tag(product_description: str, aggregate_searches: int, baseline_searches: int,
              source_authorized: bool, followers: int = 0) -> dict:
    """TAG 02: aggregate trend candidate; followers do not imply reach.

    Only authorized public/aggregate signals are accepted. No individual profile data.
    """
    terms = normalize_terms(product_description)
    current = max(0, int(aggregate_searches))
    baseline = max(0, int(baseline_searches))
    growth = (current + 1) / (baseline + 1)
    return {
        "tag_type": "aggregate_trend",
        "terms": list(terms),
        "growth_ratio": round(growth, 2),
        "high_audience_signal": max(0, int(followers)) >= 1_000_000,
        "eligible": bool(source_authorized and terms and current >= 20 and growth >= 2),
        "distribution_authorized": False,
    }


def match_catalog(tag: dict, offers: list[dict], limit: int = 20) -> list[dict]:
    """Rank approved real offers in memory; never fabricate catalog entries."""
    terms = set(tag.get("terms", []))
    if not tag.get("eligible") or not terms:
        return []
    matches = []
    for offer in offers:
        if not offer.get("active", False) or not offer.get("approved", False):
            continue
        words = set(normalize_terms(str(offer.get("title", ""))))
        score = len(terms & words)
        if score:
            matches.append((score, offer))
    matches.sort(key=lambda entry: (-entry[0], str(entry[1].get("id", ""))))
    return [offer for _, offer in matches[:max(0, min(limit, 50))]]
