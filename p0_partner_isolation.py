"""Fail-closed partner isolation for Werozinha storefront.

Authorization requires BOTH active offer and active partner; destination host
validation remains the responsibility of main.validate_authorized_url.
No inference from brand names, affiliate accounts or unverified links.
"""


def eligible_partner_offer(row):
    """Only publish database-authorized active offers with a stable partner ID."""
    if row.get("offer_active") is not True or row.get("partner_active") is not True:
        return False
    partner_id = row.get("partner_id")
    offer_id = row.get("id")
    if isinstance(partner_id, bool) or isinstance(offer_id, bool):
        return False
    if not isinstance(partner_id, int) or partner_id <= 0:
        return False
    if not isinstance(offer_id, int) or offer_id <= 0:
        return False
    if not isinstance(row.get("partner_name"), str) or not row["partner_name"].strip():
        return False
    if not isinstance(row.get("domain"), str) or not row["domain"].strip():
        return False
    if not isinstance(row.get("authorized_url"), str) or not row["authorized_url"].strip():
        return False
    return True
