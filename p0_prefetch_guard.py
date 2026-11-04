"""Exclude explicit browser prefetch/prerender from landing counters.

This is a traffic-quality heuristic only, not proof of a human visitor or
authenticated campaign source. No network calls, DB access or identifiers.
"""


def should_count_landing_visit(headers) -> bool:
    for name in ("purpose", "sec-purpose", "x-moz"):
        value = headers.get(name, "")
        if isinstance(value, str) and any(
            hint in value.casefold() for hint in ("prefetch", "prerender")
        ):
            return False
    return True
