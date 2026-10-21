"""Offline-first affiliate campaign gate. No network, database or publication side effects."""
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse, parse_qs

class Decision(str, Enum):
    READY = "READY_FOR_REVIEW"
    QUARANTINED = "QUARANTINED"

@dataclass(frozen=True)
class Offer:
    product_id: str
    url: str
    affiliate_ref: str
    affiliation_authorized: bool
    checkout_ref_verified: bool
    media_rights_confirmed: bool
    media_public_url: str = ""

@dataclass(frozen=True)
class GateResult:
    decision: Decision
    reasons: tuple[str, ...]

def evaluate(offer: Offer) -> GateResult:
    reasons = []
    p = urlparse(offer.url)
    refs = parse_qs(p.query).get("ref", [])
    if p.scheme != "https" or not p.netloc or refs != [offer.affiliate_ref] or not offer.affiliate_ref:
        reasons.append("affiliate_url_invalid")
    if not offer.affiliation_authorized:
        reasons.append("affiliation_not_authorized")
    if not offer.checkout_ref_verified:
        reasons.append("checkout_attribution_unverified")
    if not offer.media_rights_confirmed:
        reasons.append("media_rights_unverified")
    media = urlparse(offer.media_public_url)
    if media.scheme != "https" or not media.netloc:
        reasons.append("public_media_missing")
    return GateResult(Decision.QUARANTINED if reasons else Decision.READY, tuple(reasons))

def publication_payload(offer: Offer, approved: bool) -> dict:
    gate = evaluate(offer)
    if gate.decision != Decision.READY or not approved:
        raise ValueError("Publication blocked: " + ",".join(gate.reasons or ("human_approval_missing",)))
    return {"media": [offer.media_public_url], "affiliate_url": offer.url,
            "disclosure": "Publicidade | Link de afiliado",
            "idempotency_key": f"{offer.product_id}:{offer.affiliate_ref}"}
