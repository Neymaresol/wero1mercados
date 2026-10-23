# PARADIGMA — Double Check P0 (2026-10-19, America/Sao_Paulo)

## Evidence
- Render wero1mercados production latest live deployment: 2026-10-16, commit `05b8f3e44b8cabe75221ffa01f8275ab802fc8c2` (PR #85 Amazon attribution).
- Render Wero1all production latest live deployment: 2026-10-13, commit `1b1ccc458b5a463a671dcfbaeda6c28223095973`.
- Render Wero1 has no deployment history returned.
- Neon project `wero1mercados-staging` has offers, clicks, conversions and reconciliation tables; **it is not proof of the production database**.
- Neon project `wero1-operario` has robot_registry and transactions tables.
- README references v1.6.0-BR; verify runtime version before updating documentation.

## Mandatory P0 gates before production
1. Identify effective production database through redacted Render configuration and read-only SQL; never print connection strings or tokens.
2. Verify GET-only health/version endpoints and read-only catalog, active offers, attribution status and analytics. Do not call /go, /out, tracking or mutation endpoints as probes.
3. Verify all authorized affiliate destinations and Amazon tag / Shopee attribution without generating synthetic clicks.
4. Reconcile real sales and commissions exclusively with authenticated provider records, keeping pending and confirmed distinct.
5. Verify Render logs, uptime, startup/shutdown frequency, error rate and database connectivity.
6. Run isolated integration tests and Double Check on staging; validate rollback and canary before any production release.
7. Record service version, deploy SHA, date/time, environment, health and evidence source in dashboard.

## Blockers
- P0 production database source unverified.
- P0 provider-confirmed sales/commissions unverified.
- P0 real end-to-end attribution unverified.
- P0 uninterrupted health/heartbeat unverified.

No production changes or real clicks are authorized by this document.
