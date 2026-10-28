"""Fail-closed advisory INT ranking. Not connected to production or posting.

Only the server-side authenticated ingestion layer may set source_authenticated.
Unverified GET redirects, client-provided campaign labels and click totals are
not evidence of INT.1 or INT.2. No database writes or network calls.
"""
from collections.abc import Mapping
from hotmart_intent_funnel import IntentEvent, classify


def eligible_int_ranking(offers, events_by_offer, *, source_authenticated=False, limit=12):
    """Return eligible offers ordered by authenticated INT tier, then stable ID.

    A caller MUST verify source identity and event authenticity before passing
    source_authenticated=True. Missing or invalid evidence fails closed.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
        raise ValueError("invalid limit")
    if source_authenticated is not True:
        return []
    if not isinstance(events_by_offer, Mapping):
        return []
    eligible = []
    for offer in offers:
        if not isinstance(offer, Mapping):
            continue
        offer_id = offer.get("offer_id")
        if type(offer_id) is not int or offer_id <= 0:
            continue
        if offer.get("active") is not True or offer.get("partner_active") is not True:
            continue
        if offer.get("affiliate_authorized") is not True:
            continue
        events = events_by_offer.get(offer_id, ())
        if not isinstance(events, (list, tuple)) or any(
            not isinstance(e, IntentEvent) or e.trusted is not True for e in events
        ):
            continue
        tier = classify(events)
        if tier == "NONE":
            continue
        eligible.append({"offer_id": offer_id, "intent_tier": tier})
    eligible.sort(key=lambda row: (-{"INT.1": 1, "INT.2": 2}[row["intent_tier"]], row["offer_id"]))
    return eligible[:limit]
