"""Build tracked internal offer URLs; no network or database access."""
import re
from urllib.parse import urlencode

ALLOWED_CHANNELS = frozenset({"social", "facebook", "instagram", "tiktok", "direct"})
CAMPAIGN_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

def tracked_werozinha_target(offer_id: int, channel: str = "social", campaign: str = "werozinha-amazon") -> str:
    if type(offer_id) is not int or offer_id <= 0:
        raise ValueError("invalid offer")
    if channel not in ALLOWED_CHANNELS or not CAMPAIGN_RE.fullmatch(campaign):
        raise ValueError("invalid attribution")
    return f"/campanha/werozinha/amazon/{offer_id}?" + urlencode({"channel": channel, "campaign": campaign})
