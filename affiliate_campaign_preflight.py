"""Read-only campaign preflight: no HTTP requests, database writes or publishing."""
from dataclasses import dataclass
from affiliate_funnel_release_gate import validate_affiliate_destination

@dataclass(frozen=True)
class Campaign:
    partner: str
    offer_url: str
    offer_active: bool
    partner_approved: bool
    attribution_verified: bool
    media_type: str
    network: str

def check_campaign(campaign: Campaign):
    """Fail closed: validation is necessary, not proof of platform approval."""
    checks = {
        "authorized_destination_format": validate_affiliate_destination(campaign.partner, campaign.offer_url),
        "active_offer": campaign.offer_active,
        "partner_approval": campaign.partner_approved,
        "attribution_verified": campaign.attribution_verified,
        "tiktok_media_supported": campaign.network != "tiktok" or campaign.media_type in {"image/jpeg", "image/webp", "video/mp4"},
    }
    return {"ready_to_submit_for_review": all(checks.values()), "checks": checks,
            "note": "Manual/platform approval and policy review remain required; never auto-publish on this signal."}
