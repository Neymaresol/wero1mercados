import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from decimal import Decimal
import secrets
from fastapi.responses import RedirectResponse

VERSION = "1.6.5-BR"
SERVICE = "wero1mercados"
DATABASE_URL = os.getenv("DATABASE_URL", "")
WERO_ADMIN_TOKEN = os.getenv("WERO_ADMIN_TOKEN", "")

app = FastAPI(title=SERVICE, version=VERSION)
admin_bearer = HTTPBearer(auto_error=False)


def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL nao configurada")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS partners (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                domain TEXT NOT NULL UNIQUE,
                active BOOLEAN NOT NULL DEFAULT TRUE
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id BIGSERIAL PRIMARY KEY,
                partner_id BIGINT NOT NULL REFERENCES partners(id),
                title TEXT NOT NULL,
                authorized_url TEXT NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id BIGSERIAL PRIMARY KEY,
                slug TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id BIGSERIAL PRIMARY KEY,
                category_id BIGINT REFERENCES categories(id),
                sku TEXT UNIQUE,
                title TEXT NOT NULL,
                brand TEXT,
                description TEXT,
                market TEXT NOT NULL DEFAULT 'BR',
                currency TEXT NOT NULL DEFAULT 'BRL',
                active BOOLEAN NOT NULL DEFAULT TRUE,
                source TEXT NOT NULL DEFAULT 'authorized_partner',
                last_validated_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS product_offers (
                id BIGSERIAL PRIMARY KEY,
                product_id BIGINT NOT NULL REFERENCES products(id),
                partner_id BIGINT NOT NULL REFERENCES partners(id),
                authorized_url TEXT NOT NULL,
                price_brl NUMERIC(14,2),
                commission_brl NUMERIC(14,2),
                available BOOLEAN NOT NULL DEFAULT TRUE,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                source_updated_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(product_id, partner_id, authorized_url)
            )
            """)
            # Deterministic repair for the legacy category collision.
            # Preserve the canonical appliance row and move the mislabeled row
            # to eletronicos-celulares. If a canonical electronics row already
            # exists, move product references to it and deactivate the duplicate.
            cur.execute("""
                SELECT id FROM categories
                 WHERE slug='eletrodomesticos' AND name='Eletrônicos e Celulares'
                 ORDER BY id LIMIT 1
            """)
            legacy_electronics = cur.fetchone()
            cur.execute("""
                SELECT id FROM categories
                 WHERE slug='eletronicos-celulares'
                 ORDER BY id LIMIT 1
            """)
            canonical_electronics = cur.fetchone()
            if legacy_electronics:
                legacy_id = legacy_electronics["id"]
                if canonical_electronics and canonical_electronics["id"] != legacy_id:
                    cur.execute(
                        "UPDATE products SET category_id=%s WHERE category_id=%s",
                        (canonical_electronics["id"], legacy_id),
                    )
                    cur.execute("UPDATE categories SET active=FALSE WHERE id=%s", (legacy_id,))
                else:
                    cur.execute(
                        """UPDATE categories
                              SET slug='eletronicos-celulares',
                                  name='Eletrônicos e Celulares',
                                  active=TRUE
                            WHERE id=%s""",
                        (legacy_id,),
                    )

            cur.executemany("""
                INSERT INTO categories(slug, name, active)
                VALUES(%s, %s, TRUE)
                ON CONFLICT(slug) DO UPDATE SET name=EXCLUDED.name, active=TRUE
            """, [
                ("eletronicos-celulares", "Eletrônicos e Celulares"),
                ("informatica", "Informatica"),
                ("casa-cozinha", "Casa e Cozinha"),
                ("eletrodomesticos", "Eletrodomesticos"),
                ("beleza-cuidados-pessoais", "Beleza e Cuidados Pessoais"),
                ("moda-acessorios", "Moda e Acessorios"),
                ("ferramentas", "Ferramentas"),
                ("automotivo", "Automotivo"),
                ("esportes", "Esportes"),
                ("pet", "Pet"),
                ("cursos-produtos-digitais", "Cursos e Produtos Digitais"),
                ("servicos", "Servicos"),
            ])
            cur.execute("SELECT id FROM categories WHERE slug=%s", ("eletronicos-celulares",))
            canonical = cur.fetchone()
            cur.execute("SELECT id FROM categories WHERE slug=%s", ("eletrodomésticos",))
            legacy = cur.fetchone()
            if legacy and canonical and legacy["id"] != canonical["id"]:
                cur.execute("UPDATE products SET category_id=%s WHERE category_id=%s", (canonical["id"], legacy["id"]))
                cur.execute("UPDATE categories SET active=FALSE WHERE id=%s", (legacy["id"],))
            cur.execute("CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, active)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_products_market_active ON products(market, active)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_product_offers_product_active ON product_offers(product_id, active, available)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_product_offers_partner_active ON product_offers(partner_id, active, available)")
            cur.execute("""
            ALTER TABLE offers ADD COLUMN IF NOT EXISTS product_id BIGINT REFERENCES products(id)
            """)
            cur.execute("""
            ALTER TABLE offers ADD COLUMN IF NOT EXISTS price_brl NUMERIC(14,2)
            """)
            cur.execute("""
            ALTER TABLE offers ADD COLUMN IF NOT EXISTS commission_brl NUMERIC(14,2)
            """)
            cur.execute("""
            ALTER TABLE offers ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'authorized_partner'
            """)
            cur.execute("""
            ALTER TABLE offers ADD COLUMN IF NOT EXISTS source_updated_at TIMESTAMPTZ
            """)
            cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_offers_product_partner_url
            ON offers(product_id, partner_id, authorized_url)
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
                id BIGSERIAL PRIMARY KEY,
                offer_id BIGINT NOT NULL REFERENCES offers(id),
                channel TEXT NOT NULL DEFAULT 'direct',
                campaign TEXT NOT NULL DEFAULT '',
                robot_id TEXT NOT NULL DEFAULT 'wero1mercados',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS conversions (
                id BIGSERIAL PRIMARY KEY,
                external_id TEXT NOT NULL UNIQUE,
                offer_id BIGINT REFERENCES offers(id),
                status TEXT NOT NULL,
                sale_amount_brl NUMERIC(14,2),
                commission_brl NUMERIC(14,2),
                confirmed_at TIMESTAMPTZ
            )
            """)

        # psycopg connection context closes the connection but an explicit
        # commit here makes startup schema/data migrations unambiguous.
        conn.commit()

@app.on_event("startup")
def startup():
    init_db()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


@app.get("/health")
def health():
    database_ok = False
    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                database_ok = cur.fetchone() is not None
    except Exception:
        database_ok = False
    return {
        "status": "ok" if database_ok else "degraded",
        "service": SERVICE,
        "version": VERSION,
        "market": "BR",
        "currency": "BRL",
        "storage": "postgresql",
        "storage_persistent": database_ok,
        "database_ok": database_ok,
        "time": now_iso(),
    }


@app.get("/")
def root():
    return {
        "service": SERVICE,
        "version": VERSION,
        "status": "homologation",
        "market": "BR",
        "currency": "BRL",
        "message": "wero1mercados Brasil",
    }


@app.get("/api/categories")
def list_categories():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, slug, name, active
                FROM categories
                WHERE active=TRUE
                ORDER BY name
            """)
            rows = cur.fetchall()
    return {"market": "BR", "categories": rows}


@app.get("/api/admin/diagnostics/categories")
def diagnose_categories(_admin: None = Depends(require_admin)):
    """Read-only category/schema diagnostics. Never returns connection strings or secrets."""
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database() AS database, current_schema() AS schema")
            location = cur.fetchone()
            cur.execute("""
                SELECT id, slug, name, active,
                       length(slug) AS slug_length,
                       encode(convert_to(slug, 'UTF8'), 'hex') AS slug_utf8_hex,
                       length(name) AS name_length,
                       encode(convert_to(name, 'UTF8'), 'hex') AS name_utf8_hex
                  FROM categories
                 WHERE id IN (1, 4)
                    OR slug IN ('eletrodomesticos', 'eletronicos-celulares')
                 ORDER BY id
            """)
            rows = cur.fetchall()
            cur.execute("""
                SELECT conname, contype, pg_get_constraintdef(oid) AS definition
                  FROM pg_constraint
                 WHERE conrelid='categories'::regclass
                 ORDER BY conname
            """)
            constraints = cur.fetchall()
            cur.execute("""
                SELECT indexname, indexdef
                  FROM pg_indexes
                 WHERE schemaname=current_schema()
                   AND tablename='categories'
                 ORDER BY indexname
            """)
            indexes = cur.fetchall()
    return {
        "service": SERVICE,
        "version": VERSION,
        "database": location["database"],
        "schema": location["schema"],
        "categories": rows,
        "constraints": constraints,
        "indexes": indexes,
        "secrets_exposed": False,
    }


@app.get("/api/products")
def list_products(
    category: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=100, ge=1, le=500),
):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pr.id, pr.sku, pr.title, pr.brand, pr.description,
                       pr.market, pr.currency, pr.source, pr.last_validated_at,
                       c.slug AS category_slug, c.name AS category_name,
                       COUNT(po.id) FILTER (WHERE po.active=TRUE) AS active_offers,
                       MIN(po.price_brl) FILTER (WHERE po.active=TRUE) AS best_price_brl
                FROM products pr
                LEFT JOIN categories c ON c.id=pr.category_id
                LEFT JOIN offers po ON po.product_id=pr.id
                WHERE pr.active=TRUE
                  AND pr.market='BR'
                  AND (%s::text IS NULL OR c.slug=%s)
                GROUP BY pr.id, c.slug, c.name
                ORDER BY pr.updated_at DESC, pr.id DESC
                LIMIT %s
            """, (category, category, limit))
            rows = cur.fetchall()
    return {"market": "BR", "currency": "BRL", "products": rows}


def require_admin(credentials: HTTPAuthorizationCredentials | None = Depends(admin_bearer)):
    if not WERO_ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Admin token nao configurado")
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not secrets.compare_digest(credentials.credentials, WERO_ADMIN_TOKEN)
    ):
        raise HTTPException(status_code=401, detail="Nao autorizado")


class ProductIn(BaseModel):
    sku: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=300)
    category_slug: str = Field(min_length=1, max_length=80)
    brand: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    source: str = Field(default="authorized_partner", min_length=1, max_length=120)


class OfferIn(BaseModel):
    partner_name: str = Field(min_length=1, max_length=200)
    partner_domain: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=300)
    authorized_url: str = Field(min_length=1, max_length=2000)
    sku: str = Field(min_length=1, max_length=120)
    price_brl: Decimal | None = Field(default=None, ge=0)
    commission_brl: Decimal | None = Field(default=None, ge=0)


@app.post("/api/commercial/products")
def upsert_commercial_product(payload: ProductIn, _admin: None = Depends(require_admin)):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE slug=%s AND active=TRUE", (payload.category_slug.strip().lower(),))
            category = cur.fetchone()
            if not category:
                raise HTTPException(status_code=400, detail="Categoria ativa nao encontrada")
            cur.execute("""INSERT INTO products(category_id,sku,title,brand,description,market,currency,active,source,last_validated_at,updated_at)
                VALUES(%s,%s,%s,%s,%s,'BR','BRL',TRUE,%s,NOW(),NOW())
                ON CONFLICT(sku) DO UPDATE SET category_id=EXCLUDED.category_id,title=EXCLUDED.title,brand=EXCLUDED.brand,
                description=EXCLUDED.description,active=TRUE,source=EXCLUDED.source,last_validated_at=NOW(),updated_at=NOW()
                RETURNING id""", (category["id"], payload.sku.strip(), payload.title.strip(), payload.brand, payload.description, payload.source))
            product_id = cur.fetchone()["id"]
    return {"status":"registered","product_id":product_id,"sku":payload.sku.strip(),"market":"BR","currency":"BRL"}


def validate_authorized_url(url: str, domain: str):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise HTTPException(status_code=400, detail="Destino deve usar HTTPS")
    host = (parsed.hostname or "").lower()
    expected = domain.strip().lower()
    if not expected or (host != expected and not host.endswith("." + expected)):
        raise HTTPException(status_code=400, detail="Destino nao autorizado")


@app.post("/api/commercial/offers")
def register_commercial_offer(payload: OfferIn, _admin: None = Depends(require_admin)):
    partner_name = payload.partner_name.strip()
    partner_domain = payload.partner_domain.strip().lower()
    title = payload.title.strip()
    authorized_url = payload.authorized_url.strip()
    sku = payload.sku.strip()
    validate_authorized_url(authorized_url, partner_domain)
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE sku=%s AND active=TRUE", (sku,))
            product = cur.fetchone()
            if not product:
                raise HTTPException(status_code=404, detail="Produto ativo nao encontrado")
            cur.execute("""
                INSERT INTO partners(name, domain, active) VALUES(%s,%s,TRUE)
                ON CONFLICT(domain) DO UPDATE SET name=EXCLUDED.name, active=TRUE
                RETURNING id
            """, (partner_name, partner_domain))
            partner_id = cur.fetchone()["id"]
            cur.execute("""
                INSERT INTO offers(partner_id, product_id, title, authorized_url, price_brl,
                                   commission_brl, active, source, source_updated_at)
                VALUES(%s,%s,%s,%s,%s,%s,TRUE,'authorized_partner',NOW())
                ON CONFLICT(product_id, partner_id, authorized_url)
                DO UPDATE SET title=EXCLUDED.title, price_brl=EXCLUDED.price_brl,
                              commission_brl=EXCLUDED.commission_brl, active=TRUE,
                              source='authorized_partner', source_updated_at=NOW()
                RETURNING id
            """, (partner_id, product["id"], title, authorized_url,
                  payload.price_brl, payload.commission_brl))
            offer_id = cur.fetchone()["id"]
    return {"status": "registered", "offer_id": offer_id, "financial_rule": "Valores comerciais nao contam como venda ate conversao confirmada pela fonte parceira."}


@app.get("/api/offers")
def list_offers():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id, o.product_id, o.title, o.price_brl, o.commission_brl, o.active,
                       p.id AS partner_id, p.name AS partner_name, p.domain
                FROM offers o JOIN partners p ON p.id=o.partner_id
                ORDER BY o.id DESC
            """)
            rows = cur.fetchall()
    return {"offers": rows}


@app.get("/go/{offer_id}")
def go_offer(
    offer_id: int,
    channel: str = Query(default="direct", max_length=40),
    campaign: str = Query(default="", max_length=80),
):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id, o.authorized_url, o.active, p.domain,
                       p.active AS partner_active
                FROM offers o JOIN partners p ON p.id=o.partner_id
                WHERE o.id=%s
            """, (offer_id,))
            row = cur.fetchone()
            if not row or not row["active"] or not row["partner_active"]:
                raise HTTPException(status_code=404, detail="Oferta indisponivel")

            validate_authorized_url(row["authorized_url"], row["domain"])

            cur.execute(
                """INSERT INTO clicks(offer_id,channel,campaign,robot_id,created_at)
                   VALUES(%s,%s,%s,%s,NOW())""",
                (offer_id, channel, campaign, SERVICE),
            )
            target = row["authorized_url"]
    return RedirectResponse(target, status_code=302)


@app.get("/api/commercial")
def commercial():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM offers WHERE active=TRUE")
            offers = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM clicks")
            clicks = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM conversions WHERE status='confirmed'")
            confirmed = cur.fetchone()["c"]
            cur.execute("""
                SELECT COALESCE(SUM(sale_amount_brl),0) AS sales,
                       COALESCE(SUM(commission_brl),0) AS commission
                FROM conversions WHERE status='confirmed'
            """)
            totals = cur.fetchone()
    return {
        "service": SERVICE,
        "version": VERSION,
        "market": "BR",
        "currency": "BRL",
        "active_offers": offers,
        "clicks": clicks,
        "confirmed_sales": confirmed,
        "confirmed_sales_brl": float(totals["sales"]),
        "confirmed_commission_brl": float(totals["commission"]),
        "financial_rule": "Somente conversoes confirmadas pela fonte parceira.",
    }
