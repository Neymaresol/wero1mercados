# P0 Commercial Double Check — 2026-10-13 (BRT)

Scope: Wero1Mercados only. Production must remain untouched.

## Implementation
- scripts/p0_database_identity.py checks DATABASE_URL syntax without printing credentials, host, database or raw URL. Optional HMAC fingerprint requires DB_DIAGNOSTIC_KEY (>=32 characters); use the same key in staging and production only through secret management for comparison.
- tests/test_p0_funnel_provenance_20261013.py checks config redaction, static GET /go/ and POST /out/ contract, and partner report provenance offline. **Static checks are not live route integration tests.**
- p0_conversion_gate.py supplies a fail-closed adapter for verified official reports. **Not wired to the production endpoint**: current /api/commercial/conversions/provider still accepts admin-authenticated payloads and must not be considered proof of partner-originated revenue.

## Staging Double Check required before any merge
1. Verify staging DATABASE_URL points to staging Postgres, never production; compare optional keyed fingerprints safely. Do not log credentials or host.
2. Run all unit tests and CI; build container; inspect /health and /api/commercial with staging data.
3. In an isolated ephemeral Postgres database, test GET /go/{id} records exactly one landing and no click; POST /out/{id} records exactly one click and returns 303 to a preapproved test domain. Test inactive, missing and malicious offers.
4. Confirm verified Amazon/Shopee/Mercado Livre reports require operator-authenticated provenance and matching SHA256; reject duplicates, altered reports and forbidden state transitions. Confirm cancellation/reversal subtracts from confirmed totals.
5. Before enabling any production conversion ingestion, replace or disable the legacy administrative write path or restrict it to explicitly unverified staging records. Do not count it as confirmed.
6. Inspect Render config without disclosing secrets; compare effective database fingerprint with intended environment. Verify backup, canary, rollback and health.

## Rollback
Do not migrate production or modify live service in this PR. If staging checks fail, revert branch changes or deploy previous staging image; leave production unchanged.

## Known limitations
The effective production database was not identified by this change. No live production clicks, sales or commissions were generated or confirmed. No staging deploy was triggered by this PR.
