"""P0 gate for trusted affiliate report ingestion. Fail closed by default.

The current administrative conversion endpoint MUST NOT be treated as verified
partner evidence. No authenticated partner adapter is integrated; a caller-set
`verified=True` flag and a matching file hash are not proof of source identity.
"""
from provider_reconciliation import Provenance, official_adapter

# Explicitly closed until a server-side adapter authenticates partner origin.
AUTHENTICATED_ADAPTER_AVAILABLE = False


def verified_rows(*, partner, raw, provenance, columns):
    if not isinstance(provenance, Provenance) or provenance.verified is not True:
        raise ValueError("authenticated partner provenance required")
    if provenance.partner != partner:
        raise ValueError("partner identity mismatch")
    if not AUTHENTICATED_ADAPTER_AVAILABLE:
        raise PermissionError("authenticated partner adapter not integrated")
    return official_adapter(partner, raw, provenance, columns)


def reject_unverified_manual_conversion(*_args, **_kwargs):
    raise PermissionError("manual conversion is not authenticated partner evidence")
