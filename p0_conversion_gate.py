"""P0 gate for trusted affiliate report ingestion. Fail closed by default.

The current administrative conversion endpoint MUST NOT be treated as verified
partner evidence. This gate is for future adapter integration in staging.
"""
from provider_reconciliation import Provenance, official_adapter

def verified_rows(*, partner, raw, provenance, columns):
    if not isinstance(provenance, Provenance) or provenance.verified is not True:
        raise ValueError("authenticated partner provenance required")
    if provenance.partner != partner:
        raise ValueError("partner identity mismatch")
    return official_adapter(partner, raw, provenance, columns)

def reject_unverified_manual_conversion(*_args, **_kwargs):
    raise PermissionError("manual conversion is not authenticated partner evidence")
