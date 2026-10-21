"""Safe, read-only commercial evidence classification.

Do not infer affiliate attribution or sales from redirect HTTP status codes.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    redirect_observed: bool
    tag_syntax_valid: bool
    partner_account_tag_verified: bool
    partner_report_authenticated: bool
    partner_conversion_confirmed: bool

    def status(self) -> str:
        if not self.redirect_observed:
            return "NO_REDIRECT_EVIDENCE"
        if not self.tag_syntax_valid:
            return "INVALID_AFFILIATE_TAG"
        if not self.partner_account_tag_verified:
            return "AFFILIATE_OWNERSHIP_UNVERIFIED"
        if not self.partner_report_authenticated:
            return "PARTNER_REPORT_NOT_AUTHENTICATED"
        if not self.partner_conversion_confirmed:
            return "NO_PARTNER_CONFIRMED_SALE"
        return "PARTNER_CONFIRMED_SALE"
