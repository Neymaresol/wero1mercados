"""Fail-closed Amazon affiliate tracking tag guard.

No tags are synthesized or substituted. A syntactically valid tag is not proof
of Amazon Associates account ownership or credited commission.
"""
import re
from urllib.parse import parse_qs, urlsplit

_TAG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,79}$")
_HOSTS = {"amazon.com.br", "www.amazon.com.br"}


def amazon_affiliate_tag(url: str) -> str | None:
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname not in _HOSTS
                or parsed.username is not None or parsed.password is not None
                or parsed.port not in (None, 443)):
            return None
        tags = parse_qs(parsed.query, keep_blank_values=True).get("tag", [])
        if len(tags) != 1 or not _TAG.fullmatch(tags[0]):
            return None
        return tags[0]
    except (TypeError, ValueError):
        return None
