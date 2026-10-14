"""Explicit staging-only persistence for vetted Shopee affiliate drafts.

Caller supplies a psycopg-compatible connection to an ISOLATED staging DB.
No connection string is read here; production execution is refused.
"""
from integrations.shopee_bulk import prepare_batch

def persist_shopee_batch(connection, records, *, environment, dry_run=True):
    if environment != "staging":
        raise ValueError("Shopee batch writes are permitted only in staging")
    if connection is None:
        raise ValueError("explicit staging database connection required")
    with connection.cursor() as cursor:
        cursor.execute("SELECT authorized_url FROM offers WHERE partner_id IN "
                       "(SELECT id FROM partners WHERE domain = %s)",
                       ("shopee.com.br",))
        existing = {row[0] for row in cursor.fetchall()}
        drafts, rejects = prepare_batch(records, existing_urls=existing)
        if dry_run:
            return {"prepared": len(drafts), "inserted": 0, "rejected": rejects, "dry_run": True}
        cursor.execute("SELECT id, active FROM partners WHERE domain = %s", ("shopee.com.br",))
        partner = cursor.fetchone()
        if partner is None or partner[1] is not False:
            raise ValueError("inactive Shopee partner must be provisioned in staging first")
        inserted = 0
        for draft in drafts:
            cursor.execute(
                "INSERT INTO offers (partner_id,title,authorized_url,active,product_id,"
                "price_brl,commission_brl,source) "
                "SELECT %s,%s,%s,FALSE,NULL,NULL,NULL,%s "
                "WHERE NOT EXISTS (SELECT 1 FROM offers WHERE authorized_url=%s) "
                "RETURNING id",
                (partner[0], draft["title"], draft["authorized_url"],
                 draft["source"], draft["authorized_url"]))
            if cursor.fetchone():
                inserted += 1
        # No implicit commit: transaction ownership stays with the caller.
        return {"prepared": len(drafts), "inserted": inserted, "rejected": rejects, "dry_run": False}
