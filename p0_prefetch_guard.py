"""Filter declared browser prefetch/prerender requests from landing counters.

This is a traffic-quality heuristic, NOT proof of a human visitor or source.
No network calls, database access, cookies, IPs, or user-agent storage.
"""


def should_count_landing_visit(headers) -> bool:
    """False only for explicit prefetch/prerender hints; other GETs remain unverified."""
    for name in ("purpose", "sec-purpose", "x-moz"):
        value = headers.get(name, "")
        if isinstance(value, str) and any(
            hint in value.casefold() for hint in ("prefetch", "prerender")
        ):
            return False
    return True
