# Wero1Mercados — Render PostgreSQL to Neon migration
Status: PREPARATION ONLY. No cutover performed.
Date: 2026-10-21 (America/Sao_Paulo)
Source: Render PostgreSQL dpg-db2h93h7lnhs73ev17og-a (expires 2026-11-05 15:32 UTC)
Destination: Neon project wero1mercados-production / long-tooth-35390946 / PostgreSQL 17
Current Render production: srv-db2fvq4s728c73cahjq0
Staging Neon: floral-hat-53843763 (MUST NOT USE FOR PRODUCTION)

## Verified source tables
catalog_visits, categories, clicks, conversions, offer_landing_visits, offers, partners,
premium_change_log, premium_settings, product_offers, products.
At preparation: 20 offers, 19 active, 77 clicks, 0 conversions.
Live writes continue; these counts are NOT a final snapshot.

## Required gates
1. Confirm free-tier capacity for the project and keep spend at zero.
2. Obtain source consistent logical backup (pg_dump --format=custom) with credentials handled only by approved secret store. Never commit dumps, PII, passwords or URLs to GitHub.
3. Validate backup archive and source schema, constraints, indexes, sequences, extension compatibility. Retain encrypted backup securely.
4. Restore into empty Neon production database using pg_restore --no-owner --no-acl (or equivalent). DO NOT run application startup before restore if it seeds demo offers.
5. Verify row counts and deterministic per-table checksums, foreign keys, indexes and sequence setval. Verify all offers and attribution URLs without triggering GET /go or POST /out.
6. Deploy isolated staging pointing at a NON-production Neon branch or separate test project; exercise health, catalog, route contract, legitimate redirects, attribution, provider-only reconciliation and rollback.
7. Coordinate a short write-freeze/maintenance window or use verified change-data-capture; otherwise clicks and visits may be lost between backup and cutover.
8. Capture final delta/consistent snapshot; verify source/destination equality and rollback readiness.
9. Only after explicit final GO LIVE approval: update production DATABASE_URL via Render secure environment variables, trigger controlled deploy, monitor /health and read-only metrics. NEVER expose credentials in logs.
10. Keep Render PostgreSQL untouched as rollback until stability confirmed. Validate click counts and commissions exclusively from provider evidence.

## Current blockers
- No backup/restore has been executed; Neon destination contains no migrated data.
- Production may be receiving writes, so copying once without a write freeze risks lost clicks.
- Restore credential path and exact free-tier quota need validation.
- No authorization yet to switch DATABASE_URL or create paid services.

## Sales continuity
Keep existing Render service and current database running throughout preparation. Do not generate synthetic visits/clicks or claim commissions. Avoid user-facing downtime; publish no unapproved campaigns.
