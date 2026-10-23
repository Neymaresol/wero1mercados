# PARADIGMA — Organic expansion approval queue
Last revision: 2026-10-21 17:30 America/Sao_Paulo (planning reference; not deployment time)
State: DRAFT / NOT APPROVED / DO NOT PUBLISH

## Verified observations
- Metricool NeyMareSol (brand 7259526), 2026-10-01 to 2026-11-15: 11 Facebook PUBLISHED, 3 Facebook ERROR (LeadLovers blocked by Community Standards), 1 TikTok ERROR (PNG media rejected), 0 future scheduled.
- Production database read-only: Amazon Brasil amazon.com.br 19 active offers; link.amazon 1 inactive; no Shopee/Hotmart partners in partners table.
- No provider-confirmed commission established by this audit.

## Release gates (ALL required for each offer)
1. Partner program approval verified with provider; link provenance documented and valid for the connected affiliate account.
2. Offer active and approved; redirect destination verified without generating synthetic /go or /out clicks.
3. Exact affiliate attribution preserved through Werozinha to merchant checkout; no misleading claim of direct sale by Werozinha.
4. Privacy, platform advertising disclosures and network-specific creative format validated.
5. Human approval of each final copy and media; no automatic publication before approval.
6. Provider-based sale/commission reconciliation only; zero fabricated sales.
7. Rate limits, platform anti-spam compliance, deduplication, opt-out and rollback validated.
8. Isolated staging Double Check and owner GO LIVE decision. No changes to production from this plan.

## Campaign queue (copy suggestions only)
| Priority | Robot | Channel | Campaign | State | Blocker |
|---|---|---|---|---|---|
| P0 | Wero1Mercados Amazon | Facebook | Curated electronics / Werozinha vitrine | DRAFT | Human approval, link attribution check |
| P0 | Wero1Mercados Amazon | TikTok | Werozinha product showcase | BLOCKED | Convert existing PNG to JPEG/WebP and validate media |
| P0 | Wero1Mercados Shopee | Facebook/TikTok | Approved Shopee products | BLOCKED | Provider authorization, offer catalog, affiliate links, staging |
| P0 | Wero1Mercados Hotmart | Facebook/TikTok | Approved digital courses | BLOCKED | Provider authorization, offer catalog, affiliate links, staging |
| P1 | Wero1Gammer | Facebook/TikTok | Gaming PCs: Premium/Ouro/Prata and peripherals | DRAFT | Supplier/stock/price evidence and checkout authorization |
| P1 | Wero1all / Wero1 Pai | Facebook | Educational automation marketing | BLOCKED | LeadLovers destination flagged by Meta; do not republish blocked URL |
| P2 | Wero1Divulgacao | Internal | Scheduling/orchestration | INTERNAL | Staging, scheduling approval workflow |
| P2 | Wero1Eletrico | Facebook | Electrical niche informational campaign | BLOCKED | Scope, compliance and authorized offer source |
| P2 | Wero1Operario | Internal | 24/7 operations health and release gates | INTERNAL | Not a sales campaign |

## Suggested compliant captions — NOT PUBLISHED
### Amazon
"🤖🧡 A Werozinha reúne opções de eletrônicos para você comparar características e disponibilidade diretamente na loja. Explore a vitrine: https://wero1mercados.onrender.com/vitrine\nPublicidade: links de afiliado podem gerar comissão por compras qualificadas. #Werozinha #Tecnologia"

### Shopee
"🛍️ Conheça ofertas selecionadas na Werozinha e confira preços e disponibilidade na loja parceira. [INSERIR URL DE OFERTA AUTORIZADA APÓS VALIDAÇÃO]\nPublicidade: podemos receber comissão por compras qualificadas. #Achadinhos"

### Hotmart
"📚 Explore cursos digitais selecionados e confira detalhes antes de decidir. [INSERIR URL DE OFERTA AUTORIZADA APÓS VALIDAÇÃO]\nPublicidade: podemos receber comissão por compras qualificadas. #CursosOnline"

### Wero1Gammer
"🎮 Compare opções gamer Premium, Ouro e Prata, além de placas de vídeo e periféricos. Consulte especificações e preços atualizados antes de comprar. [INSERIR VITRINE APROVADA]"

## Guardrails
No ads budget, no publication, no new affiliate enrollment, no production merge, no provider financial simulation, no synthetic clicks. Every campaign remains DRAFT until independently approved.
