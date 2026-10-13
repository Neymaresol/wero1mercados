"""Read-only, credential-safe P0 funnel breakdown for selected real offers.

No outbound HTTP calls, conversion creation, or synthetic click events. This
module only reads existing rows from the *application's own* PostgreSQL.
"""
from collections import defaultdict
from urllib.parse import parse_qs, urlsplit

EXPECTED_AMAZON_TAG = "wero1mercados-20"


def _valid_url(url, domain, validator):
    try:
        validator(url, domain)
        return True
    except (Exception,):
        # Diagnostic must fail closed for invalid/unparseable URLs; never
        # disclose the URL or the validation exception to the caller.
        return False


def _counts(cursor, table, ids):
    # Table is a constant controlled by this module, never request input.
    if table not in {"offer_landing_visits", "clicks"}:
        raise ValueError("unknown funnel table")
    cursor.execute(
        f"""SELECT offer_id, channel, campaign, COUNT(*) AS n
              FROM {table}
              WHERE offer_id = ANY(%s::bigint[])
              GROUP BY offer_id, channel, campaign""",
        (ids,),
    )
    return cursor.fetchall()


def audit_funnel(cursor, validator, offer_ids=(164, 802)):
    """Return aggregated evidence without sensitive URLs or visitor identifiers.

    Caller must begin a read-only database transaction and authenticate access.
    A database row marked confirmed is NOT treated as partner-verified revenue.
    """
    ids = sorted(set(int(i) for i in offer_ids))
    if not ids or len(ids) > 20 or any(i <= 0 for i in ids):
        raise ValueError("invalid offer selection")

    cursor.execute(
        """SELECT o.id, o.title, o.active, o.authorized_url,
                  p.domain, p.active AS partner_active
           FROM offers o JOIN partners p ON p.id=o.partner_id
           WHERE o.id = ANY(%s::bigint[]) ORDER BY o.id""",
        (ids,),
    )
    offers_by_id = {int(row["id"]): row for row in cursor.fetchall()}
    visits = _counts(cursor, "offer_landing_visits", ids)
    clicks = _counts(cursor, "clicks", ids)
    cursor.execute(
        """SELECT offer_id, status, COUNT(*) AS n FROM conversions
           WHERE offer_id = ANY(%s::bigint[])
           GROUP BY offer_id, status""",
        (ids,),
    )
    conversion_rows = cursor.fetchall()

    groups = defaultdict(lambda: defaultdict(lambda: {"landing_visits": 0, "outbound_records": 0}))
    for row in visits:
        groups[int(row["offer_id"])][(row["channel"], row["campaign"])]["landing_visits"] += int(row["n"])
    for row in clicks:
        groups[int(row["offer_id"])][(row["channel"], row["campaign"])]["outbound_records"] += int(row["n"])

    legacy_conversions = defaultdict(dict)
    for row in conversion_rows:
        legacy_conversions[int(row["offer_id"])][str(row["status"])] = int(row["n"])

    output = []
    for offer_id in ids:
        row = offers_by_id.get(offer_id)
        if row is None:
            output.append({"id": offer_id, "found": False, "status": "NOT_FOUND",
                           "landing_visits": 0, "outbound_records": 0,
                           "campaigns": [], "partner_verified_sales": None})
            continue
        domain = row["domain"]
        url = row["authorized_url"]
        active = bool(row["active"] and row["partner_active"])
        valid_url = _valid_url(url, domain, validator)
        amazon = domain == "amazon.com.br"
        try:
            amazon_tag_ok = parse_qs(urlsplit(url).query).get("tag") == [EXPECTED_AMAZON_TAG] if amazon else None
        except (TypeError, ValueError):
            amazon_tag_ok = False if amazon else None

        campaign_rows = []
        for (channel, campaign), nums in sorted(groups[offer_id].items(), key=lambda entry: (str(entry[0][0]), str(entry[0][1]))):
            # GET-based one-click redirect can be visited by bots/prefetchers.
            # Preserve those records but do not label them human-confirmed.
            method_class = ("UNVERIFIED_GET_REDIRECT"
                            if channel == "social" and campaign == "werozinha-amazon"
                            else "RECORDED_POST_OUTBOUND")
            campaign_rows.append({"channel": channel, "campaign": campaign,
                                  "landing_visits": nums["landing_visits"],
                                  "outbound_records": nums["outbound_records"],
                                  "outbound_evidence": method_class})
        landing_total = sum(x["landing_visits"] for x in campaign_rows)
        outbound_total = sum(x["outbound_records"] for x in campaign_rows)
        if not active or not valid_url:
            diagnosis = "NOT_AUTHORIZED"
        elif amazon and not amazon_tag_ok:
            diagnosis = "AMAZON_ASSOCIATE_TAG_NOT_MATCHED"
        elif landing_total == 0 and outbound_total == 0:
            diagnosis = "NO_TRACKED_ACTIVITY"
        elif outbound_total == 0:
            diagnosis = "NO_RECORDED_OUTBOUND"
        else:
            diagnosis = "PARTNER_CONVERSION_NOT_RECONCILED"

        output.append({
            "id": offer_id, "title": row["title"], "found": True,
            "active_authorized_url": active and valid_url,
            "partner_domain": domain,
            "amazon_associate_tag_matches_expected": amazon_tag_ok,
            "landing_visits": landing_total,
            "outbound_records": outbound_total,
            "campaigns": campaign_rows,
            "legacy_conversion_rows_unverified": legacy_conversions[offer_id],
            "partner_verified_sales": None,
            "partner_verified_commission_brl": None,
            "diagnosis": diagnosis,
        })

    return {
        "source": "application_database_connection",
        "scope": "aggregated_existing_events_only",
        "offers": output,
        "financial_provenance": "partner_report_not_authenticated_by_this_audit",
        "note": "Recorded visits/clicks may include bots or test traffic; do not infer human buyers or actual sales.",
    }
