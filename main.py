import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse

VERSION = "1.3.1-BR"
SERVICE = "wero1mercados"
DATABASE_URL = os.getenv("DATABASE_URL", "")

app = FastAPI(title=SERVICE, version=VERSION)


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
                       COUNT(po.id) FILTER (WHERE po.active=TRUE AND po.available=TRUE) AS active_offers,
                       MIN(po.price_brl) FILTER (WHERE po.active=TRUE AND po.available=TRUE) AS best_price_brl
                FROM products pr
                LEFT JOIN categories c ON c.id=pr.category_id
                LEFT JOIN product_offers po ON po.product_id=pr.id
                WHERE pr.active=TRUE
                  AND pr.market='BR'
                  AND (%s IS NULL OR c.slug=%s)
                GROUP BY pr.id, c.slug, c.name
                ORDER BY pr.updated_at DESC, pr.id DESC
                LIMIT %s
            """, (category, category, limit))
            rows = cur.fetchall()
    return {"market": "BR", "currency": "BRL", "products": rows}


@app.get("/api/offers")
def list_offers():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id, o.title, o.active,
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

            parsed = urlparse(row["authorized_url"])
            if parsed.scheme != "https":
                raise HTTPException(status_code=400, detail="Destino deve usar HTTPS")
            host = (parsed.hostname or "").lower()
            domain = row["domain"].strip().lower()
            if not domain or (host != domain and not host.endswith("." + domain)):
                raise HTTPException(status_code=400, detail="Destino nao autorizado")

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
