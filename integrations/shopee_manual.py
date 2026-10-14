"""Safe Shopee affiliate-link intake for Wero1Mercados.

Manual-link mode: no scraping, API credentials, auto-redirect or fake conversions.
Only publish links explicitly supplied by the affiliate and approved for use.
"""
from dataclasses import dataclass
from urllib.parse import urlparse

_ALLOWED_HOSTS = frozenset({"shopee.com.br", "www.shopee.com.br", "shope.ee", "s.shopee.com.br"})

@dataclass(frozen=True)
class ShopeeAffiliateOffer:
    title: str
    affiliate_url: str
    approved: bool = False
    affiliate_account: str = "neymaresol724"

    def validate(self) -> None:
        parsed = urlparse(self.affiliate_url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in _ALLOWED_HOSTS:
            raise ValueError("Shopee URL must be HTTPS and use an approved Shopee host")
        if parsed.username or parsed.password or not self.title.strip():
            raise ValueError("Invalid offer details")

    def public_link(self) -> str | None:
        self.validate()
        return self.affiliate_url if self.approved else None
