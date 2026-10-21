"""Side-effect-free release gates for affiliate funnel and Hotmart INT.1/INT.2.

This module never sends HTTP requests, records clicks, creates conversions or changes a bank.
It is deliberately NOT wired to production until staged integration is reviewed.
"""
from urllib.parse import urlparse, parse_qs
from hotmart_intent_funnel import IntentEvent, classify, allowed_hotlink

def validate_affiliate_destination(partner, url):
    """Fail closed; domain checks are exact, not suffix-based."""
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            return False
        if parsed.port not in (None, 443):
            return False
        host = parsed.hostname.lower()
        if partner == "hotmart":
            return allowed_hotlink(url)
        if partner == "amazon":
            return host in {"www.amazon.com.br", "amazon.com.br"} and bool(parse_qs(parsed.query).get("tag"))
        if partner == "shopee":
            return host in {"s.shopee.com.br", "shopee.com.br", "www.shopee.com.br"}
        return False
    except (ValueError, TypeError):
        return False

def intent_tier(landing_id, detail_id, trusted_landing=False, trusted_detail=False):
    """Only independent server-authenticated events count towards INT.2."""
    return classify([
        IntentEvent("campaign_landing", trusted_landing, landing_id),
        IntentEvent("offer_detail", trusted_detail, detail_id),
    ])

def release_gate(partner, url, *, authorized=False, source_verified=False,
                 redirect_tested=False, reconciliation_tested=False,
                 rollback_tested=False, staging_isolated=False):
    checks = {
        "affiliate_destination": validate_affiliate_destination(partner, url),
        "partner_authorization": bool(authorized),
        "trusted_event_source": bool(source_verified),
        "redirect_go_out": bool(redirect_tested),
        "provider_reconciliation": bool(reconciliation_tested),
        "rollback": bool(rollback_tested),
        "staging_isolation": bool(staging_isolated),
    }
    return {"go_live": all(checks.values()), "checks": checks,
            "financial_confirmation": "PROVIDER_ONLY"}
