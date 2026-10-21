"""Offline Hotmart INT.1/INT.2 funnel prototype; no external side effects."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
import re

@dataclass(frozen=True)
class IntentEvent:
    kind: str
    trusted: bool
    event_id: str

def classify(events):
    """Distinct trusted event IDs required; untrusted and zero-score events are ignored."""
    by_id = {}
    for event in events:
        if event.trusted and event.event_id and event.event_id not in by_id:
            by_id[event.event_id] = event.kind
    kinds = set(by_id.values())
    if {"campaign_landing", "offer_detail"} <= kinds:
        return "INT.2"
    if "campaign_landing" in kinds:
        return "INT.1"
    return "NONE"

def allowed_hotlink(url):
    try:
        p = urlparse(url)
        return (p.scheme == "https" and p.hostname == "go.hotmart.com"
                and p.username is None and p.password is None
                and p.port in (None, 443)
                and re.fullmatch(r"/G[0-9A-Za-z]+", p.path) is not None
                and not p.fragment)
    except (ValueError, TypeError):
        return False

def simulate_retained_commission(gross, rate):
    """Offline-only hypothetical result; never a provider-confirmed commission."""
    try:
        gross, rate = Decimal(str(gross)), Decimal(str(rate))
    except InvalidOperation as exc:
        raise ValueError("invalid amount or rate") from exc
    if not gross.is_finite() or not rate.is_finite() or gross < 0 or not 0 <= rate <= 1:
        raise ValueError("invalid amount or rate")
    amount = gross * rate
    return {"environment": "SIMULATION", "sale": "SIMULATED",
            "commission": str(amount.quantize(Decimal("0.01"))),
            "commission_status": "SIMULATED_RETAINED",
            "bank_transfer": "NOT_REQUESTED", "provider_confirmed": False}
