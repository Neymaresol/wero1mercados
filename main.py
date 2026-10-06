import os
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse

VERSION = "1.1.0-BR"
SERVICE = "wero1mercados"
DB_PATH = os.getenv("DB_PATH", "/tmp/wero1mercados.db")

app = FastAPI(title=SERVICE, version=VERSION)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            domain TEXT NOT NULL UNIQUE,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            authorized_url TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(partner_id) REFERENCES partners(id)
        );
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER NOT NULL,
            channel TEXT NOT NULL DEFAULT 'direct',
            campaign TEXT NOT NULL DEFAULT '',
            robot_id TEXT NOT NULL DEFAULT 'wero1mercados',
            created_at TEXT NOT NULL,
            FOREIGN KEY(offer_id) REFERENCES offers(id)
        );
        CREATE TABLE IF NOT EXISTS conversions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT NOT NULL UNIQUE,
            offer_id INTEGER,
            status TEXT NOT NULL,
            sale_amount_brl REAL,
            commission_brl REAL,
            confirmed_at TEXT,
            FOREIGN KEY(offer_id) REFERENCES offers(id)
        );
        """)


@app.on_event("startup")
def startup():
    init_db()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": SERVICE,
        "version": VERSION,
        "market": "BR",
        "currency": "BRL",
        "storage": "sqlite",
        "storage_persistent": not DB_PATH.startswith("/tmp/"),
        "time": now_iso(),
    }


@app.get("/")
def root():
    return {
        "service": SERVICE,
        "version": VERSION,
        "status": "development",
        "market": "BR",
        "currency": "BRL",
        "message": "wero1mercados Brasil",
    }


@app.get("/api/offers")
def list_offers():
    with db() as conn:
        rows = conn.execute("""
            SELECT o.id, o.title, o.active,
                   p.id AS partner_id, p.name AS partner_name, p.domain
            FROM offers o JOIN partners p ON p.id=o.partner_id
            ORDER BY o.id DESC
        """).fetchall()
    return {"offers": [dict(r) for r in rows]}


@app.get("/go/{offer_id}")
def go_offer(
    offer_id: int,
    channel: str = Query(default="direct", max_length=40),
    campaign: str = Query(default="", max_length=80),
):
    with db() as conn:
        row = conn.execute("""
            SELECT o.id, o.authorized_url, o.active, p.domain, p.active AS partner_active
            FROM offers o JOIN partners p ON p.id=o.partner_id
            WHERE o.id=?
        """, (offer_id,)).fetchone()
        if not row or not row["active"] or not row["partner_active"]:
            raise HTTPException(status_code=404, detail="Oferta indisponivel")

        parsed = urlparse(row["authorized_url"])
        if parsed.scheme != "https":
            raise HTTPException(status_code=400, detail="Destino deve usar HTTPS")

        host = (parsed.hostname or "").lower()
        domain = row["domain"].strip().lower()
        if not domain or (host != domain and not host.endswith("." + domain)):
            raise HTTPException(status_code=400, detail="Destino nao autorizado")

        conn.execute(
            "INSERT INTO clicks(offer_id,channel,campaign,robot_id,created_at) VALUES(?,?,?,?,?)",
            (offer_id, channel, campaign, SERVICE, now_iso()),
        )
        conn.commit()
        target = row["authorized_url"]

    return RedirectResponse(target, status_code=302)


@app.get("/api/commercial")
def commercial():
    with db() as conn:
        offers = conn.execute("SELECT COUNT(*) c FROM offers WHERE active=1").fetchone()["c"]
        clicks = conn.execute("SELECT COUNT(*) c FROM clicks").fetchone()["c"]
        confirmed = conn.execute(
            "SELECT COUNT(*) c FROM conversions WHERE status='confirmed'"
        ).fetchone()["c"]
        totals = conn.execute("""
            SELECT COALESCE(SUM(sale_amount_brl),0) sales,
                   COALESCE(SUM(commission_brl),0) commission
            FROM conversions WHERE status='confirmed'
        """).fetchone()
    return {
        "service": SERVICE,
        "version": VERSION,
        "market": "BR",
        "currency": "BRL",
        "active_offers": offers,
        "clicks": clicks,
        "confirmed_sales": confirmed,
        "confirmed_sales_brl": totals["sales"],
        "confirmed_commission_brl": totals["commission"],
        "financial_rule": "Somente conversoes confirmadas pela fonte parceira.",
    }
