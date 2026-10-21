# Hotmart → TikTok automation (design, 2026-10-21)

Status: development only; no production deployment.

## Objective
Discover eligible, explicitly authorized affiliate products, validate their tracked destination and checkout, create truthful compliant creatives, submit for approval, schedule through Metricool, and reconcile verified conversions without inventing sales.

## State machine
DISCOVERED → AFFILIATION_PENDING → AUTHORIZED → LINK_PENDING → LINK_VALIDATED → CREATIVE_READY → APPROVAL_PENDING → SCHEDULED → PUBLISHED → RECONCILED.
Failure or uncertainty → QUARANTINED; never publish.

## Hard gates
1. Import only affiliate products for which authorization and a valid affiliate tracking URL can be established through a permitted source; never assume the full Hotmart catalog is authorized.
2. Check allowed landing URL, HTTP destination, reference preservation, and checkout flow with safe read-only checks. Do not create an order, payment, simulated click, or conversion on live platforms.
3. Use product-owner-permitted photos/video only. Do not scrape or republish images without rights. Label sponsored affiliate promotion.
4. Enforce Hotmart and TikTok promotion rules, rate limits, content accuracy, and human approval until verified authorization for automatic posting.
5. Metricool TikTok requires a publicly accessible media URL. A local sandbox video path is NOT publicly accessible. Upload only via an authorized media hosting integration.
6. Store deduplication keys, campaign identifiers, provider publication IDs, and failures. Exponential backoff and dead-letter queue.
7. Real sales and commissions must be sourced from authenticated provider statements/webhooks with verified provenance; no estimated values as confirmed.
8. Use separate staging database and mocks. No changes to Render production DATABASE_URL; Render Free PG expiry 2026-11-05 requires separate migration plan.

## Example known offer
- Product: Especialista em Degradê — Faby Cardoso
- Affiliate URL: https://www.cursomanicure.com/degrade/?ref=G108129576P
- Checkout attribution: NOT YET independently confirmed.
- Publication: TikTok NOT YET published; video locally generated but not hosted publicly.
- Hotmart Facebook campaign: held in Metricool draft pending validation.

## Offline test scenarios
- Authorized link + valid checkout + permitted media + approval => schedule request mock succeeds.
- Redirect strips ref => quarantine.
- Checkout does not preserve attribution => quarantine.
- Unknown affiliation => quarantine.
- Media not hosted => no scheduling.
- Duplicate product => idempotent no-op.
- Provider timeout/429 => retry, bounded.
- Unauthorized webhook => reject, do not mark commission.
- Provider-verified conversion => confirmed ledger event only once.
- Rollback => existing live service unaffected.

## Next implementation tasks
Build adapters for permitted Hotmart catalog/affiliate authorization, link validation, media hosting, Metricool publication, and authenticated conversion ingestion. Integrate feature flags OFF by default; run unit and staging integration tests and Double Check before a reviewed PR/deploy.
