"""Offline Hotmart INT.1/INT.2 funnel prototype. No external side effects."""
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlparse

@dataclass(frozen=True)
class IntentEvent:
    kind: str
    trusted: bool
    event_id: str

def classify(events):
    """Return interest tier only for distinct, trusted, server-collected events."""
    kinds = {e.kind for e in events if e.trusted and e.event_id}
    if "offer_detail" in kinds and "campaign_landing" in kinds:
        return "INT.2"
    if "campaign_landing" in kinds:
        return "INT.1"
    return "NONE"

def allowed_hotlink(url):
    p = urlparse(url)
    return p.scheme == "https" and p.hostname == "go.hotmart.com" and p.username is None and p.password is None and p.port in (None, 443) and p.path.startswith("/G")

def simulate_retained_commission(gross, rate):
    """Explicitly simulated only; NEVER persist as provider-confirmed revenue."""
    amount = Decimal(str(gross)) * Decimal(str(rate))
    if amount < 0 or Decimal(str(rate)) > 1:
        raise ValueError("invalid amount or rate")
    return {"environment":"SIMULATION", "sale":"SIMULATED", "commission":str(amount.quantize(Decimal("0.01"))), "commission_status":"SIMULATED_RETAINED", "bank_transfer":"NOT_REQUESTED", "provider_confirmed":False}
