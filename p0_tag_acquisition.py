"""PARADIGMA TAG 01/02: deterministic campaign attribution; no external API calls."""
from urllib.parse import urlparse

# Channel labels are untrusted metadata, never evidence of a verified referral.
ALLOWED_CHANNELS = frozenset({"google", "chatgpt", "bing", "organic", "instagram", "facebook", "tiktok", "creator", "direct", "campaign", "catalogo"})
SEARCH_CHANNELS = frozenset({"google", "chatgpt", "bing", "organic"})
SOCIAL_CHANNELS = frozenset({"instagram", "facebook", "tiktok", "creator"})

def classify_channel(channel: str) -> str:
    """Treat incoming channel as an unverified campaign label, not proven referrer."""
    value = (channel or "direct").strip().lower()
    return value if value in ALLOWED_CHANNELS else "direct"

def tag_for_channel(channel: str) -> str:
    value = classify_channel(channel)
    if value in SEARCH_CHANNELS:
        return "TAG_01"
    if value in SOCIAL_CHANNELS:
        return "TAG_02"
    return "DIRECT"

def safe_campaign(value: str) -> str:
    """Allow only printable campaign identifiers; never include a raw URL or secrets."""
    value = (value or "").strip()
    if len(value) > 80 or not value or any(not (c.isascii() and (c.isalnum() or c in "-_")) for c in value):
        return ""
    return value

def internal_landing(offer_id: int, channel: str, campaign: str = "") -> str:
    """Build an internal offer landing, never a direct partner or affiliate URL."""
    from urllib.parse import urlencode
    if not isinstance(offer_id, int) or isinstance(offer_id, bool) or offer_id <= 0:
        raise ValueError("invalid offer")
    query = {"channel": classify_channel(channel)}
    campaign = safe_campaign(campaign)
    if campaign:
        query["campaign"] = campaign
    return "/go/" + str(offer_id) + "?" + urlencode(query)
