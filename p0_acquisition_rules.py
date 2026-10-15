"""Deterministic commercial-funnel decision rules (no database writes)."""


def acquisition_decision(*, active_offers: int, ranked_clicks: int,
                         pending_conversions: int, confirmed_sales: int):
    """Only click-bearing authorized offers enter the campaign queue.

    Active offers and clicks eligible for ranking are different metrics.
    Do not confuse an empty ranking with an empty catalog.
    """
    if active_offers <= 0:
        return "NO_ACTIVE_OFFERS", "IMPORT_AUTHORIZED_OFFERS"
    if ranked_clicks <= 0:
        return "NO_TRACKED_TRAFFIC", "DISTRIBUTE_TRACKED_CAMPAIGNS"
    if pending_conversions <= 0 and confirmed_sales <= 0:
        return "NO_CONVERSION_SIGNAL", "OPTIMIZE_OFFER_AND_LANDING"
    if confirmed_sales <= 0:
        return "PENDING_WITHOUT_CONFIRMED_SALE", "VERIFY_PROVIDER_AND_OPTIMIZE_CONVERSION"
    return "FUNNEL_CONVERTING", "SCALE_WINNERS"
