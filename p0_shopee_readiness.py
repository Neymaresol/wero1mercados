"""P0 Shopee readiness: SELECT-only, fail-closed evidence.

No affiliate click or partner API is invoked.
"""
from urllib.parse import urlparse

def inspect_shopee(cur):
    cur.execute("""
        SELECT o.id, o.active AS offer_active, p.active AS partner_active,
               p.domain, o.authorized_url
        FROM offers o JOIN partners p ON p.id=o.partner_id
        WHERE p.name = %s ORDER BY o.id
    """, ("Shopee Brasil",))
    rows = cur.fetchall()
    result = []
    for row in rows:
        url = row["authorized_url"] or ""
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        domain = (row["domain"] or "").lower()
        safe = parsed.scheme == "https" and parsed.username is None and parsed.password is None and parsed.port in (None, 443) and domain == "shopee.com.br" and (host == domain or host.endswith("." + domain))
        result.append({"offer_id": row["id"], "partner_active": bool(row["partner_active"]), "offer_active": bool(row["offer_active"]), "destination_allowed": safe, "ready_for_traffic": bool(row["partner_active"] and row["offer_active"] and safe), "attribution_verified": False})
    return {"partner": "Shopee Brasil", "offers": result, "attribution_verified": False, "production_release_approved": False, "note": "Affiliate attribution requires external provider evidence; never infer from active flags."}
