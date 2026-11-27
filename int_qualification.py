"""Fail-closed INT.1/INT.2 qualification gate.

Production has no authenticated, persisted event evidence pipeline for INT.1/INT.2.
Do not infer qualified intent from clicks, views, public scores, campaign labels,
or caller-supplied booleans/event IDs. Keep this gate closed until a separately
reviewed server-side evidence adapter is implemented and tested.
"""

INT_GATE_STATUS = "BLOCKED_NO_VERIFIED_EVENT_PIPELINE"


def filter_int_qualified_offers(offers, evidence_by_offer=None):
    """Never promote offers as INT-qualified without a trusted server-side source.

    evidence_by_offer is intentionally ignored: arbitrary mappings (including
    source_authenticated=True) cannot establish event provenance. A future
    implementation must validate stored events, offer binding, uniqueness,
    ordering, replay protection, and issuer authenticity server-side.
    """
    return []
