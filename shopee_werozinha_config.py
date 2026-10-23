"""Shopee Werozinha affiliate landing configuration (staging-only until approved)."""
from urllib.parse import urlsplit

SHOPEE_WEROZINHA_URL = "https://s.shopee.com.br/5q8zszhUm7"
SHOPEE_SUB_ID = "wero1mercados"

def validate_shopee_link(url: str) -> bool:
    """Accept only the exact merchant-generated affiliate shortlink, no lookalikes."""
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname == "s.shopee.com.br"
        and parsed.username is None
        and parsed.password is None
        and parsed.port is None
        and parsed.path == "/5q8zszhUm7"
        and not parsed.query
        and not parsed.fragment
    )

def shopee_werozinha_ready() -> bool:
    """Static URL validation is NOT provider attribution or commission confirmation."""
    return validate_shopee_link(SHOPEE_WEROZINHA_URL)
