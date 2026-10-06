import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse

VERSION = "1.2.0-BR"
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
