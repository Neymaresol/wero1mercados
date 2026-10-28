"""Isolated PostgreSQL ledger for verified partner conversions.

No connection is made on import. Caller supplies a staging connection and must
verify report provenance before invoking upsert. Never wired to production.
"""
from decimal import Decimal
import re
from provider_reconciliation import PARTNERS, STATUSES, reconcile

DDL = """
CREATE TABLE IF NOT EXISTS affiliate_conversion_ledger (
 source_partner TEXT NOT NULL,
 source_account TEXT NOT NULL,
 external_id TEXT NOT NULL,
 source_report TEXT NOT NULL,
 source_sha256 CHAR(64) NOT NULL,
 status TEXT NOT NULL CHECK (status IN ('pending','confirmed','reversed','cancelled')),
 sale_amount_brl NUMERIC(14,2) NOT NULL CHECK (sale_amount_brl >= 0),
 commission_brl NUMERIC(14,2) NOT NULL CHECK (commission_brl >= 0),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 PRIMARY KEY(source_partner, source_account, external_id)
);
CREATE TABLE IF NOT EXISTS affiliate_conversion_audit (
 id BIGSERIAL PRIMARY KEY,
 source_partner TEXT NOT NULL,
 source_account TEXT NOT NULL,
 external_id TEXT NOT NULL,
 previous_status TEXT,
 new_status TEXT NOT NULL,
 source_report TEXT NOT NULL,
 source_sha256 CHAR(64) NOT NULL,
 changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

def install_schema(conn):
    """Explicit migration in staging only. Not called automatically."""
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()

def upsert_verified(conn, row):
    """Transactional idempotent write; caller controls connection and provenance.

    Use with a dedicated transaction and a role limited to the ledger schema.
    On error, rollback the transaction; no other tables are modified.
    """
    required = {"source_partner", "source_account", "external_id", "source_report",
                "source_sha256", "status", "sale_amount_brl", "commission_brl"}
    if not required.issubset(row) or row["status"] not in STATUSES:
        raise ValueError("invalid verified conversion")
    if not all(isinstance(row[k], str) and row[k].strip() for k in required):
        raise ValueError("missing conversion field")
    if row["source_partner"] not in PARTNERS:
        raise ValueError("unapproved source partner")
    if re.fullmatch(r"[0-9a-f]{64}", row["source_sha256"]) is None:
        raise ValueError("invalid source checksum")
    for key in ("sale_amount_brl", "commission_brl"):
        amount = Decimal(row[key])
        if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
            raise ValueError("invalid amount")
    identity = (row["source_partner"], row["source_account"], row["external_id"])
    with conn.cursor() as cur:
        # Lock a deterministic partner/account scope to serialize first inserts.
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                    (row["source_partner"] + ":" + row["source_account"],))
        cur.execute("""SELECT source_partner,source_account,external_id,source_report,
                       source_sha256,status,sale_amount_brl,commission_brl
                       FROM affiliate_conversion_ledger
                       WHERE source_partner=%s AND source_account=%s AND external_id=%s
                       FOR UPDATE""", identity)
        previous = cur.fetchone()
        if previous:
            keys = ["source_partner","source_account","external_id","source_report",
                    "source_sha256","status","sale_amount_brl","commission_brl"]
            old = dict(zip(keys, previous)) if not isinstance(previous, dict) else previous
            old = {**old, "sale_amount_brl": str(old["sale_amount_brl"]),
                   "commission_brl": str(old["commission_brl"])}
            reconcile(old, row)
            if (old["status"],old["sale_amount_brl"],old["commission_brl"]) == (
                row["status"],row["sale_amount_brl"],row["commission_brl"]):
                return "unchanged"
            cur.execute("""UPDATE affiliate_conversion_ledger
                SET status=%s,sale_amount_brl=%s,commission_brl=%s,
                    source_report=%s,source_sha256=%s,updated_at=NOW()
                WHERE source_partner=%s AND source_account=%s AND external_id=%s""",
                (row["status"],row["sale_amount_brl"],row["commission_brl"],
                 row["source_report"],row["source_sha256"],*identity))
        else:
            cur.execute("""INSERT INTO affiliate_conversion_ledger
                (source_partner,source_account,external_id,source_report,source_sha256,
                 status,sale_amount_brl,commission_brl)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                tuple(row[k] for k in ("source_partner","source_account","external_id",
                    "source_report","source_sha256","status","sale_amount_brl","commission_brl")))
        cur.execute("""INSERT INTO affiliate_conversion_audit
            (source_partner,source_account,external_id,previous_status,new_status,source_report,source_sha256)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (*identity, old["status"] if previous else None, row["status"],
             row["source_report"],row["source_sha256"]))
    return "updated" if previous else "inserted"

def confirmed_totals(conn):
    """Reversals and cancellations are excluded from confirmed revenue."""
    with conn.cursor() as cur:
        cur.execute("""SELECT COUNT(*),COALESCE(SUM(sale_amount_brl),0),
                       COALESCE(SUM(commission_brl),0)
                       FROM affiliate_conversion_ledger WHERE status='confirmed'""")
        return cur.fetchone()
