"""Fail-closed INT.1/INT.2 qualification gate.

No independently authenticated, persisted event adapter is available.
Never infer intent from clicks, views, public scores, campaign labels,
caller-supplied booleans or event IDs.
"""

INT_GATE_STATUS = "BLOCKED_NO_VERIFIED_EVENT_PIPELINE"


def filter_int_qualified_offers(offers, evidence_by_offer=None):
    """Keep the INT-qualified list empty until a trusted server adapter exists.

    evidence_by_offer is intentionally ignored: mappings and caller flags do
    not establish issuer identity, offer binding, event uniqueness, ordering,
    persistence or replay protection.
    """
    return []
