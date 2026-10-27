# P0 — Render PostgreSQL continuity, provenance and promotion gate

**Audit baseline:** 2026-10-27 06:18 BRT (09:18 UTC)  
**Scope:** Wero1Mercados / Wero1Divulgação only.  
**Status:** RUNBOOK ONLY — no backup, restore, deploy, merge, production test event or payment has been executed by this document.

## Verified infrastructure baseline (read-only)

- Render production service: `srv-db2fvq4s728c73cahjq0`, branch `main`, commit `80018a1c3b4a41d8bb052ddf798b11b10d613afa`, deploy status `live`.
- Render production PostgreSQL: `dpg-db2h93h7lnhs73ev17og-a`, status `available`, version 18.6.
- Free database expiry: **2026-11-05 15:32:30 UTC / 12:32:30 BRT**. This is a provider-reported deadline, not a completed migration.
- Service `healthCheckPath` is empty; `autoDeploy=yes`, `autoDeployTrigger=commit`. **Never merge to `main` as a staging test.**
- Database IP allow list currently includes `0.0.0.0/0`. Do not change access rules until the app connectivity path is verified and a safe rollback exists.
- On 2026-10-27 09:18 UTC, a read-only database query succeeded. One additional session was observed, but its client identity was not established. This **does not** prove that the production application is connected to PostgreSQL.
- Render application logs at 08:22 UTC recorded Uvicorn startup complete; a `HEAD /campanha/werozinha` request returned HTTP 405. Neither event verifies `/health` or `/ready`.
- Render production schema: 11 public tables; Neon staging schema: 13 (two extra affiliate audit/ledger tables). **Do not equate the two databases.**
- The latest checked Render staging deploy is `9a3741d`, not the P0 correction branch. Neon staging is PostgreSQL 17; production Render is PostgreSQL 18.

## P0 continuity and recovery gate — before 2026-11-05

1. Identify the **effective** production database connection from the running application without exposing `DATABASE_URL` or credentials. Use service logs or a controlled `/ready` check; SQL access from the auditor alone is insufficient.
2. In an approved secure operator environment, obtain a consistent `pg_dump --format=custom` backup of **Render production PostgreSQL 18**. Keep the archive in approved secure storage, not in GitHub or a public URL. Do not log secrets. Record the backup timestamp, SHA-256 checksum, object size and retention location.
3. Validate the archive with `pg_restore --list`; then **restore into an isolated PostgreSQL 18 test database** with no partner callbacks, no real publication and no external payment processing. Merely listing an archive is not a restore test. Do not provision a paid database or incur charges without separate approval.
4. Compare schema, row counts and critical foreign keys after restore. Verify the `offers`, `clicks`, `conversions`, `offer_landing_visits` and `catalog_visits` tables. Do not write synthetic sales, commissions or transfers. If restore is impossible, record a **BLOCKER** rather than claiming a usable backup.
5. Record the tested recovery time, rollback target, operator and expiry decision. Do not change plans or delete the free instance automatically.

## P0 application + provenance gate

1. Confirm `GET /health` responds successfully and `GET /ready` reports **503** when the *staging* DB is unavailable, without modifying production. If DNS or access fails, mark health as **unverified**, not necessarily down.
2. Run the correction branch in **isolated Render staging** connected only to its designated staging DB. Verify that the deployed commit SHA matches the tested commit. The existing staging deployment is outdated.
3. Test `GET /go/{offer_id}` and `POST /out/{offer_id}` with isolated test data only. **GET /go may record a landing visit; POST /out records a click.** Do not probe either route with fake activity in production. Do not follow redirects to live affiliate partners during tests.
4. Verify that invalid, inactive or unauthorized partner URLs fail closed. Confirm that legacy GET campaign routes do **not** record clicks; verify `POST /out` requires explicit confirmation. A POST is not cryptographic proof of a human.
5. Reject unauthenticated provider conversion ingestion **before** any write to `conversions`. A click, redirect, social impression or affiliate label is not a verified sale or commission.
6. Test that INT.1 **and** INT.2 must each have positive, independently authorized evidence. Exclude zero-score or forged-signal offers from actionable ranking; keep `campaign_queue=[]` without verified evidence.
7. Confirm the public/authorized source of each signal and partner affiliation. Metricool account `@neymaresoloficial` must not be treated as `@neymaresol`.
8. For attribution, use approved campaign identifiers and authorized redirect links. Existing Shopee Facebook post links directly to Shopee, bypassing internal `/go`/`/out`; do not infer internal funnel conversions from its impressions.

## Promotion / rollback Double Check

- GitHub CI on **the final candidate commit** passes; offline tests and HTTP staging tests pass; audit/provenance checks pass.
- Backup **restored successfully**, database identity proven, health/readiness observed, schema compatibility reviewed, and rollback procedure tested.
- Explicitly control Render `main` auto-deploy before any merge; do not merge while it can unexpectedly deploy to production.
- Canary, health and data integrity checks succeed before traffic migration; rollback target remains available.
- No paid ads, new charges, fabricated engagement, simulated production sales, or changes to Wero1Operário/Wero1Elétrico.

## Read-only evidence queries

```sql
SELECT current_database(), current_setting('server_version'), now();
SELECT count(*) FROM offers;
SELECT count(*) FROM clicks;
SELECT count(*) FROM conversions;
SELECT application_name, client_addr::text, state, backend_start
  FROM pg_stat_activity WHERE datname=current_database();
```

**Open blockers as of this baseline:** verified restore, application-to-database identity, live HTTP health/readiness, updated isolated staging deploy, integrated `/go`/`/out` HTTP test, final-candidate CI, and safe production rollback.
