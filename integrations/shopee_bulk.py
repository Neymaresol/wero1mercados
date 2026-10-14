"""Safe, side-effect-free Shopee affiliate bulk intake for staging.

Input records must come from the account holder or an authorized Shopee export.
No scraping, API credentials, automatic publication or synthetic commissions.
"""
from dataclasses import dataclass
from urllib.parse import urlparse

_ALLOWED = {"shopee.com.br", "www.shopee.com.br", "s.shopee.com.br", "shope.ee"}

@dataclass(frozen=True)
class Candidate:
    title: str
    affiliate_url: str
    source: str = "affiliate_manual"
    approved: bool = False

def prepare_batch(records, existing_urls=(), max_batch=500):
    """Return (inactive drafts, rejects), without touching any database."""
    records = list(records)
    if len(records) > max_batch:
        raise ValueError("batch limit exceeded")
    seen = set(existing_urls)
    drafts, rejects = [], []
    for index, record in enumerate(records):
        try:
            if not isinstance(record, dict):
                raise ValueError("record must be an object")
            title = record.get("title", "")
            url = record.get("affiliate_url", "")
            if not isinstance(title, str) or not title.strip() or len(title) > 300:
                raise ValueError("invalid title")
            if not isinstance(url, str):
                raise ValueError("invalid URL")
            p = urlparse(url)
            if (p.scheme != "https" or (p.hostname or "").lower() not in _ALLOWED
                    or p.username or p.password or p.port is not None
                    or not p.path or p.fragment or len(url) > 2048):
                raise ValueError("invalid Shopee affiliate URL")
            if url in seen:
                raise ValueError("duplicate URL")
            seen.add(url)
            drafts.append({"title": title.strip(), "authorized_url": url,
                           "active": False, "price_brl": None,
                           "commission_brl": None, "product_id": None,
                           "source": "affiliate_manual_pending_validation"})
        except (ValueError, TypeError) as exc:
            rejects.append({"index": index, "reason": str(exc)})
    return drafts, rejects
