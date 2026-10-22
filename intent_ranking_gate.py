"""Fail-closed eligibility for advisory rankings based on trusted INT.1/INT.2 evidence.

Raw clicks, landing-page views, and campaign labels are NOT authenticated intent.
Until a trusted provider/event pipeline supplies independently verified evidence,
the advisory ranking must not surface any offer as INT-qualified.
"""
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation


def _positive_finite(value):
    if isinstance(value, bool) or value is None:
        return False
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return False
    return number.is_finite() and number > 0


def has_verified_intent(evidence):
    """Require authenticated, distinct events and both positive intent scores."""
    if not isinstance(evidence, Mapping) or evidence.get("source_authenticated") is not True:
        return False
    landing_id = evidence.get("int1_event_id")
    detail_id = evidence.get("int2_event_id")
    if not isinstance(landing_id, str) or not landing_id.strip():
        return False
    if not isinstance(detail_id, str) or not detail_id.strip() or landing_id == detail_id:
        return False
    return (_positive_finite(evidence.get("int1_score"))
            and _positive_finite(evidence.get("int2_score")))


def filter_verified_intent_offers(offers, evidence_by_offer):
    """No verified evidence store means zero qualified offers, never guessed scores."""
    if not isinstance(evidence_by_offer, Mapping):
        return []
    return [offer for offer in offers
            if has_verified_intent(evidence_by_offer.get(offer["offer_id"]))]
