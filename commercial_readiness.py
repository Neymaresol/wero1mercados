"""Conservative readiness checks for commercial acquisition channels.

No platform connection or publication is inferred from campaign availability.
"""
from dataclasses import dataclass
from typing import Mapping

CHANNELS = ("instagram", "facebook", "tiktok", "kwai")


@dataclass(frozen=True)
class ChannelReadiness:
    channel: str
    credentials_configured: bool
    permission_verified: bool
    publishing_enabled: bool
    status: str


def assess_channels(
    credentials: Mapping[str, bool],
    permissions: Mapping[str, bool],
    enabled: Mapping[str, bool],
) -> list[ChannelReadiness]:
    """Fail closed: flags alone never prove that publishing actually works."""
    results = []
    for channel in CHANNELS:
        configured = credentials.get(channel) is True
        permitted = permissions.get(channel) is True
        requested = enabled.get(channel) is True
        if not configured:
            status = "CREDENTIALS_MISSING"
        elif not permitted:
            status = "PERMISSION_NOT_VERIFIED"
        elif not requested:
            status = "DISABLED"
        else:
            status = "READY_FOR_LIVE_VALIDATION"
        results.append(ChannelReadiness(channel, configured, permitted, requested, status))
    return results


def acquisition_gaps(*, active_offers: int, clicks: int, confirmed_sales: int) -> list[str]:
    """Diagnose observable funnel gaps without fabricating conversions."""
    if min(active_offers, clicks, confirmed_sales) < 0:
        raise ValueError("metrics must be nonnegative")
    gaps = []
    if active_offers == 0:
        gaps.append("NO_ACTIVE_OFFERS")
    if clicks == 0:
        gaps.append("NO_TRACKED_TRAFFIC")
    if confirmed_sales == 0:
        gaps.append("NO_CONFIRMED_CONVERSIONS")
    return gaps
