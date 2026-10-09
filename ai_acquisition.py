"""Wero1 AI acquisition foundation: safe, deterministic campaign recommendations.

No scraping, unsolicited messaging, or automatic posting is performed.
External model/provider adapters must be separately approved and configured.
"""
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse


@dataclass(frozen=True)
class Campaign:
    offer_id: int
    title: str
    authorized_url: str
    active: bool
    partner_active: bool


@dataclass(frozen=True)
class Recommendation:
    offer_id: int
    channel: str
    angle: str
    disclosure: str
    requires_approval: bool = True


ALLOWED_CHANNELS = frozenset({"instagram", "facebook", "tiktok", "kwai"})


def recommend_campaigns(
    campaigns: Iterable[Campaign], channel: str, *, limit: int = 12
) -> list[Recommendation]:
    """Create human-reviewable briefs only; never contact customers or post."""
    if channel not in ALLOWED_CHANNELS:
        raise ValueError("channel not authorized")
    if not 1 <= limit <= 100:
        raise ValueError("invalid limit")
    result = []
    for offer in campaigns:
        if not (offer.active and offer.partner_active):
            continue
        parsed = urlparse(offer.authorized_url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password):
            continue
        title = (offer.title or "").strip()
        if not title:
            continue
        result.append(Recommendation(
            offer_id=offer.offer_id,
            channel=channel,
            angle=f"Apresente a categoria {title} com informacoes verificadas e chamada para conhecer a oferta.",
            disclosure="Publicidade: posso receber comissao por compras qualificadas.",
        ))
        if len(result) >= limit:
            break
    return result
