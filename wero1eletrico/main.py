"""Wero1Eletrico prototype v1.0.0-BR: vehicle lead marketplace, no fake inventory or sales."""
import os
import sqlite3
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

APP_NAME = "wero1eletrico"
VERSION = "1.0.0-BR-prototype"
DB_PATH = os.getenv("WERO_ELETRICO_DB", "/tmp/wero1eletrico-prototype.db")
app = FastAPI(title=APP_NAME, version=VERSION)

def connection():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS leads (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      model_interest TEXT NOT NULL,
      city TEXT NOT NULL,
      contact_channel TEXT NOT NULL,
      consent INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'new',
      created_at TEXT NOT NULL
    )""")
    db.commit()
    return db

class Lead(BaseModel):
    model_interest: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=120)
    contact_channel: str = Field(pattern="^(whatsapp|email)$")
    consent: bool

@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "version": VERSION,
            "mode": "prototype", "time": datetime.now(timezone.utc).isoformat()}

@app.get("/api/catalog")
def catalog():
    return {"market": "BR", "segment": "electric_and_hybrid_cars",
            "vehicles": [], "message": "Nenhum estoque ou oferta de parceiro validado"}

@app.post("/api/leads", status_code=201)
def create_lead(lead: Lead):
    if not lead.consent:
        raise HTTPException(422, "Consentimento explicito obrigatorio")
    with connection() as db:
        cur = db.execute(
            "INSERT INTO leads(model_interest,city,contact_channel,consent,created_at) VALUES(?,?,?,?,?)",
            (lead.model_interest, lead.city, lead.contact_channel, 1,
             datetime.now(timezone.utc).isoformat()))
        db.commit()
        return {"lead_id": cur.lastrowid, "status": "new",
                "note": "Lead captado; nenhuma venda ou comissao confirmada"}

@app.get("/api/commercial")
def commercial():
    with connection() as db:
        leads = db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    return {"service": APP_NAME, "version": VERSION, "leads": leads,
            "partner_confirmed_sales": 0, "confirmed_commission_brl": 0,
            "integration_status": "not_connected", "mode": "prototype"}
