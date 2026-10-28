"""Offline tests: no HTTP, database writes, synthetic clicks or conversions."""
import pytest
from hotmart_intent_funnel import IntentEvent
from p0_int_ranking_gate import eligible_int_ranking


def offer(offer_id, **overrides):
    row = {"offer_id": offer_id, "active": True,
           "partner_active": True, "affiliate_authorized": True}
    row.update(overrides)
    return row


def test_unverified_source_fails_closed():
    evidence = {1: [IntentEvent("campaign_landing", True, "a")]}
    assert eligible_int_ranking([offer(1)], evidence) == []
    assert eligible_int_ranking([offer(1)], evidence, source_authenticated=1) == []


def test_zero_int_scores_never_enter_ranking():
    assert eligible_int_ranking([offer(1)], {1: []}, source_authenticated=True) == []
    assert eligible_int_ranking([offer(1)], {1: [IntentEvent("offer_detail", True, "x")]},
                                source_authenticated=True) == []


def test_untrusted_events_and_inactive_offers_excluded():
    evidence = {1: [IntentEvent("campaign_landing", False, "a")],
                2: [IntentEvent("campaign_landing", True, "b")]}
    assert eligible_int_ranking([offer(1), offer(2, active=False)], evidence,
                                source_authenticated=True) == []


def test_authenticated_int2_precedes_int1():
    evidence = {1: [IntentEvent("campaign_landing", True, "a")],
                2: [IntentEvent("campaign_landing", True, "b"),
                    IntentEvent("offer_detail", True, "c")]}
    assert eligible_int_ranking([offer(1), offer(2)], evidence,
                                source_authenticated=True) == [
        {"offer_id": 2, "intent_tier": "INT.2"},
        {"offer_id": 1, "intent_tier": "INT.1"},
    ]


def test_duplicate_event_id_does_not_create_int2():
    evidence = {1: [IntentEvent("campaign_landing", True, "same"),
                    IntentEvent("offer_detail", True, "same")]}
    assert eligible_int_ranking([offer(1)], evidence, source_authenticated=True) == [
        {"offer_id": 1, "intent_tier": "INT.1"}
    ]


def test_authorization_and_limit():
    evidence = {1: [IntentEvent("campaign_landing", True, "a")],
                2: [IntentEvent("campaign_landing", True, "b")]}
    assert eligible_int_ranking([offer(1, affiliate_authorized=False), offer(2)],
                                evidence, source_authenticated=True, limit=1) == [
        {"offer_id": 2, "intent_tier": "INT.1"}
    ]
    with pytest.raises(ValueError):
        eligible_int_ranking([], {}, source_authenticated=True, limit=0)
