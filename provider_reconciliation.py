"""Fail-closed, read-only parsing of official affiliate exports.

This module does not fetch partner APIs, accept webhooks, or mutate a database.
Every input must be accompanied by a verified provenance record established by
an authenticated operator outside this module. CSV column names are intentionally
normalized only after a partner-specific mapping is provided.
"""
import csv
import hashlib
import hmac
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping

PARTNERS = frozenset({"amazon", "shopee", "mercado_livre"})
STATUSES = frozenset({"pending", "confirmed", "reversed", "cancelled"})
MAX_BYTES = 5_000_000
MAX_ROWS = 10000

@dataclass(frozen=True)
class Provenance:
    partner: str
    account_id: str
    report_id: str
    sha256: str
    verified: bool

def parse_verified_csv(raw: bytes, provenance: Provenance, columns: Mapping[str, str]):
    """Return normalized rows without performing writes.

    The caller must independently verify report origin and bind SHA-256 to the
    actual bytes. No partner report is trusted just because it contains a name.
    """
    if not provenance.verified or provenance.partner not in PARTNERS:
        raise ValueError("unverified partner report")
    if not provenance.account_id.strip() or not provenance.report_id.strip():
        raise ValueError("missing source identity")
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("invalid report size")
    actual = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(actual, provenance.sha256.lower()):
        raise ValueError("report checksum mismatch")
    required = {"external_id", "status", "sale_amount_brl", "commission_brl"}
    if set(columns) != required or any(not x for x in columns.values()):
        raise ValueError("incomplete column mapping")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("invalid UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV headers")
    if not set(columns.values()).issubset(reader.fieldnames):
        raise ValueError("missing CSV columns")
    output = []
    seen = set()
    for index, row in enumerate(reader, 1):
        if index > MAX_ROWS or None in row:
            raise ValueError("malformed or oversized report")
        external_id = (row[columns["external_id"]] or "").strip()
        status = (row[columns["status"]] or "").strip().lower()
        if not external_id or len(external_id) > 200 or status not in STATUSES:
            raise ValueError("invalid conversion identity or status")
        try:
            amount = Decimal((row[columns["sale_amount_brl"]] or "").strip())
            commission = Decimal((row[columns["commission_brl"]] or "").strip())
        except InvalidOperation as exc:
            raise ValueError("invalid monetary amount") from exc
        if not all(x.is_finite() and x >= 0 and x.as_tuple().exponent >= -2 for x in (amount, commission)):
            raise ValueError("invalid monetary precision")
        key = (provenance.partner, provenance.account_id, external_id)
        if key in seen:
            raise ValueError("duplicate external id in report")
        seen.add(key)
        output.append({"source_partner": provenance.partner, "source_account": provenance.account_id,
                       "source_report": provenance.report_id, "external_id": external_id,
                       "status": status, "sale_amount_brl": str(amount),
                       "commission_brl": str(commission), "source_sha256": actual})
    return output

def reconcile(existing: Mapping, incoming: Mapping):
    """Pure transition check; terminal cancellations/reversals cannot be silently revived."""
    if (existing["source_partner"], existing["source_account"], existing["external_id"]) != (
        incoming["source_partner"], incoming["source_account"], incoming["external_id"]):
        raise ValueError("conversion identity mismatch")
    old, new = existing["status"], incoming["status"]
    if old not in STATUSES or new not in STATUSES:
        raise ValueError("invalid state")
    if old in {"reversed", "cancelled"} and new != old:
        raise ValueError("terminal conversion cannot be revived automatically")
    if old == "confirmed" and new == "pending":
        raise ValueError("cannot regress confirmed conversion")
    if old == new and (existing["sale_amount_brl"], existing["commission_brl"]) != (
        incoming["sale_amount_brl"], incoming["commission_brl"]):
        raise ValueError("same-status financial revision requires manual reconciliation")
    return dict(incoming)

def official_adapter(partner: str, raw: bytes, provenance: Provenance, columns: Mapping[str, str]):
    if partner != provenance.partner or partner not in PARTNERS:
        raise ValueError("partner mismatch")
    return parse_verified_csv(raw, provenance, columns)
