AMAZON_CURATED_CAMPAIGNS = [["amazon-fones-abertos-99528904011","Fones de Ouvido Abertos","eletronicos-celulares","https://www.amazon.com.br/Fones-Ouvido-Abertos/b?ie=UTF8&node=99528904011&linkCode=ll2&tag=wero1mercados-20&linkId=28a1e4536793e6973267534d85c628d3&ref_=as_li_ss_tl"],["amazon-mais-vendidos-eletronicos","Mais Vendidos em Eletrônicos","eletronicos-celulares","https://www.amazon.com.br/gp/bestsellers/electronics?ie=UTF8&linkCode=ll2&tag=wero1mercados-20&linkId=815660c212dde378628806512caafb69&ref_=as_li_ss_tl"],["amazon-eletronicos-oferta-17368183011","Eletrônicos em Oferta","eletronicos-celulares","https://www.amazon.com.br/eletronicos-em-oferta/b?ie=UTF8&node=17368183011&linkCode=ll2&tag=wero1mercados-20&linkId=669d1854d248393bec15702d5a3d54e2&ref_=as_li_ss_tl"],["amazon-informatica-16339926011","Computadores e Informática","informatica","https://www.amazon.com.br/Computadores-Informatica/b?ie=UTF8&node=16339926011&linkCode=ll2&tag=wero1mercados-20&linkId=614d91379af7ccf5efccff4c860e310f&ref_=as_li_ss_tl"],["amazon-pesquisa-full-hd","Pesquisa Full HD","eletronicos-celulares","https://www.amazon.com.br/s?k=full+hd&__mk_pt_BR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=31LUZKQO0HVGQ&sprefix=full+hd%2Caps%2C287&linkCode=ll2&tag=wero1mercados-20&linkId=c43351e6768cc2b5593c0b6f875ae7e5&ref_=as_li_ss_tl"],["amazon-categoria-16194414011","Categoria Amazon 16194414011","casa-cozinha","https://www.amazon.com.br/b?node=16194414011&linkCode=ll2&tag=wero1mercados-20&linkId=d083d534d11d95ee33a6260b9d16f961&ref_=as_li_ss_tl"],["amazon-categoria-16209062011","Categoria Amazon 16209062011","casa-cozinha","https://www.amazon.com.br/b?node=16209062011&linkCode=ll2&tag=wero1mercados-20&linkId=6dabe40af9e2d4b6b580533265d12df1&ref_=as_li_ss_tl"],["amazon-videogames-20261009","Videogames - Amazon","eletronicos-celulares","https://www.amazon.com.br/s?__mk_pt_BR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&url=search-alias%3Dvideogames&field-keywords=&crid=28VPBOJ103YOM&sprefix=%2Cvideogames%2C290&linkCode=ll2&tag=wero1mercados-20&linkId=4c83835dee6345dbcd46ded6278cc008&ref_=as_li_ss_tl"]]

import os
from datetime import datetime, timezone
from urllib.parse import urlparse, urlencode

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from decimal import Decimal
import secrets
import html
import time
from fastapi.responses import RedirectResponse, HTMLResponse

VERSION = "1.14.10-BR-rc1"
SERVICE = "wero1mercados"
DATABASE_URL = os.getenv("DATABASE_URL", "")
WERO_ADMIN_TOKEN = os.getenv("WERO_ADMIN_TOKEN", "")
WERO_MODE = os.getenv("WERO_MODE", "homologation").strip().lower()
if WERO_MODE not in {"production", "homologation"}:
    WERO_MODE = "homologation"

app = FastAPI(title=SERVICE, version=VERSION)
admin_bearer = HTTPBearer(auto_error=False)
BOOT_MONO = time.monotonic()
PERF_MODE = os.getenv("WERO_PERFORMANCE_MODE", "game").lower()
PERF = {"requests": 0, "errors": 0, "latency_ms_ema": 0.0}

@app.middleware("http")
async def performance_telemetry(request, call_next):
    start = time.perf_counter()
    PERF["requests"] += 1
    try:
        response = await call_next(request)
        return response
    except Exception:
        PERF["errors"] += 1
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        PERF["latency_ms_ema"] = round(ms if PERF["latency_ms_ema"] == 0 else PERF["latency_ms_ema"] * .85 + ms * .15, 2)

@app.get("/api/performance")
def performance():
    uptime = max(time.monotonic() - BOOT_MONO, .001)
    return {"service": SERVICE, "version": VERSION, "mode": PERF_MODE,
            "requests": PERF["requests"], "errors": PERF["errors"],
            "latency_ms_ema": PERF["latency_ms_ema"],
            "requests_per_second": round(PERF["requests"] / uptime, 3),
            "uptime_seconds": round(uptime, 1),
            "note": "Telemetria medida no processo atual; performance nao representa vendas."}


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

def seed_amazon_campaigns():
    """Idempotent publication of user-supplied SiteStripe category links."""
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO partners(name,domain,active) VALUES('Amazon Brasil','amazon.com.br',TRUE)
                ON CONFLICT(domain) DO UPDATE SET active=TRUE RETURNING id""")
            partner_id = cur.fetchone()["id"]
            for sku, title, category_slug, url in AMAZON_CURATED_CAMPAIGNS:
                validate_authorized_url(url, "amazon.com.br")
                cur.execute("SELECT id FROM categories WHERE slug=%s AND active=TRUE", (category_slug,))
                category = cur.fetchone()
                if not category:
                    raise RuntimeError("Categoria Amazon indisponivel: " + category_slug)
                cur.execute("""INSERT INTO products(category_id,sku,title,market,currency,active,source,last_validated_at,updated_at)
                    VALUES(%s,%s,%s,'BR','BRL',TRUE,'user_sitestripe',NOW(),NOW())
                    ON CONFLICT(sku) DO UPDATE SET title=EXCLUDED.title,category_id=EXCLUDED.category_id,
                    updated_at=NOW() RETURNING id""", (category["id"],sku,title))
                product_id = cur.fetchone()["id"]
                cur.execute("""INSERT INTO offers(partner_id,product_id,title,authorized_url,active,source,source_updated_at)
                    VALUES(%s,%s,%s,%s,TRUE,'user_sitestripe',NOW())
                    ON CONFLICT(product_id,partner_id,authorized_url)
                    DO UPDATE SET title=EXCLUDED.title,source_updated_at=NOW()""",
                    (partner_id,product_id,title,url))
        # Quarantine only the known legacy Kindle placeholder URL. Never touch
        # the seven authorized SiteStripe campaigns or historical click records.
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE offers o SET active=FALSE
                FROM products pr, partners pa
                WHERE o.product_id=pr.id AND o.partner_id=pa.id
                  AND pr.sku='amazon-kindle-16gb-2024'
                  AND pa.domain='link.amazon'
                  AND o.authorized_url='https://link.amazon/B0cUY7dgR'
                  AND o.active=TRUE
            """)
        conn.commit()


@app.on_event("startup")
def startup():
    init_db()
    seed_amazon_campaigns()


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


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PARADIGMA WERO — Dashboard Mestre</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#020d1a;color:#f5f8ff;font:14px Arial,sans-serif;overflow-x:hidden}.app{display:grid;grid-template-columns:210px 1fr 270px;min-height:100vh;gap:12px;padding:12px}.panel,.card{background:linear-gradient(145deg,#06182a,#03111f);border:1px solid #12395b;border-radius:14px;box-shadow:0 0 18px #006cff18}.brand{font-size:28px;font-weight:900;color:#ffd34f}.brand small{display:block;font-size:11px;letter-spacing:4px;color:white}.menu div{padding:15px;border-radius:9px;margin:5px 0}.menu .on{background:#075bd7;box-shadow:0 0 16px #087cff}.hero{min-height:150px;padding:26px;background:radial-gradient(circle at 20% 50%,#0755a7,#03111f 58%);position:relative;overflow:hidden}.hero h1{font-size:40px;letter-spacing:8px;margin:0;text-align:center}.hero h2{text-align:center;color:#ffc83d;margin:8px}.hero p{text-align:center}.prod{color:#16ee89;border:1px solid #164a50;border-radius:20px;padding:8px 14px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:12px 0}.kpi{padding:16px}.kpi b{font-size:25px;display:block;margin-top:10px}.green{color:#15ed89}.pink{color:#ff2c87}.blue{color:#38a5ff}.gold{color:#ffd34f}.mainrow{display:grid;grid-template-columns:1.2fr .9fr;gap:10px}.chart{min-height:240px;padding:16px}.bars{height:155px;display:flex;align-items:end;gap:18px;border-bottom:1px solid #23506d;padding:0 15px}.bar{width:38px;background:linear-gradient(#16ee89,#087cff);border-radius:5px 5px 0 0}.forecast{display:grid;grid-template-columns:1fr 1fr;gap:10px}.forecast div{border:1px solid #145080;border-radius:10px;padding:18px}.forecast b{display:block;font-size:20px;margin-top:7px}.robots{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:10px}.robot{padding:15px;border:1px solid #126bc4}.robot h3{margin:0 0 10px}.social{margin-top:12px;font-size:18px;word-spacing:8px}.bottom{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:10px}.bottom .card{padding:15px;min-height:155px}.right .card{padding:16px;margin-bottom:12px}.statusline{display:flex;justify-content:space-between;border-top:1px solid #15334b;padding:10px 0}.notice{padding:11px 0;border-top:1px solid #15334b}.muted{color:#94a9be;font-size:12px}.warning{font-size:11px;color:#a9bbca;margin-top:12px}.mobile-nav{display:none}
@media(max-width:900px){.app{display:block;padding:8px}.left,.right{display:none}.hero h1{font-size:28px;letter-spacing:4px}.kpis{grid-template-columns:1fr 1fr}.mainrow{grid-template-columns:1fr}.robots{grid-template-columns:1fr 1fr}.bottom{grid-template-columns:1fr}.mobile-nav{display:flex;overflow:auto;gap:8px;padding:8px;margin-bottom:8px}.mobile-nav span{white-space:nowrap;padding:10px 14px;background:#071c31;border-radius:9px}.top{padding:4px}.brand{font-size:21px}}

.pressure-title{margin:16px 0 8px;font-size:16px}.gauges{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:10px 0}.gauge{padding:14px;text-align:center;position:relative}.dial{--p:0;width:128px;height:70px;margin:8px auto 4px;overflow:hidden;position:relative}.dial:before{content:"";position:absolute;width:112px;height:112px;border-radius:50%;left:8px;top:8px;background:conic-gradient(from 270deg,#16364c 0deg,#16ee89 55deg,#ffd34f 105deg,#ff2c87 180deg,#071421 180deg);box-shadow:inset 0 0 0 13px #04111e}.needle{position:absolute;width:48px;height:3px;background:#fff;left:64px;top:62px;transform-origin:0 50%;transform:rotate(calc(-180deg + (var(--p) * 1.8deg)));transition:transform .8s cubic-bezier(.2,.8,.2,1);box-shadow:0 0 8px #fff}.needle:after{content:"";position:absolute;width:10px;height:10px;border-radius:50%;background:#fff;left:-5px;top:-4px}.pressure{font-size:22px;font-weight:900}.dial-scale{display:flex;justify-content:space-between;max-width:145px;margin:0 auto;color:#a9bbca;font-size:10px}.idle .needle{animation:idlePulse 2.2s ease-in-out infinite}@keyframes idlePulse{0%,100%{margin-top:0}50%{margin-top:-2px}}.pulse{animation:salePulse .7s ease-out}@keyframes salePulse{50%{box-shadow:0 0 28px #16ee89}}@media(max-width:900px){.gauges{grid-template-columns:1fr 1fr}.gauges .gauge:first-child{grid-column:1/-1}.dial{width:118px}}
.menu button,.mobile-nav button{background:#071c31;color:white;border:0;border-radius:9px;padding:13px;cursor:pointer;font:inherit;white-space:nowrap}.menu button{display:block;width:100%;margin:5px 0;text-align:left}.mobile-nav button[aria-current="page"],.menu button[aria-current="page"]{background:#075dbe;outline:2px solid #38a5ff}.tab-panel[hidden]{display:none!important}.tab-panel{padding:20px;margin:14px 0}.tab-panel a{color:#77c5ff}.tab-metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}.tab-metrics div{border:1px solid #145080;border-radius:9px;padding:15px}.tab-metrics b{display:block;font-size:22px;margin-top:8px}@media(max-width:900px){.mobile-nav{display:flex}}</style></head><body>
<div class="app">
<aside class="left panel" style="padding:18px"><div class="brand">♛ PARADIGMA<small>ECOSSISTEMA WERO</small></div><div class="menu"><button type="button" data-tab="dashboard">Dashboard</button><button type="button" data-tab="robots">Robôs</button><button type="button" data-tab="sales">Vendas</button><button type="button" data-tab="finance">Financeiro</button><button type="button" data-tab="reports">Relatórios</button><button type="button" data-tab="notifications">Notificações</button><button type="button" data-tab="settings">Configurações</button><button type="button" data-tab="help">Ajuda</button></div></aside>
<main><div class="top"><div class="brand">PARADIGMA <span class="gold">WERO</span></div><span class="prod">● PRODUÇÃO</span></div><nav class="mobile-nav"><button type="button" data-tab="dashboard">Dashboard</button><button type="button" data-tab="robots">Robôs</button><button type="button" data-tab="sales">Vendas</button><button type="button" data-tab="finance">Financeiro</button><button type="button" data-tab="reports">Relatórios</button><button type="button" data-tab="notifications">Notificações</button><button type="button" data-tab="settings">Configurações</button><button type="button" data-tab="help">Ajuda</button></nav>
<section class="hero panel"><h1>PARADIGMA</h1><h2>WERO</h2><p>DASHBOARD MESTRE</p><p class="muted">ROBÔS • VENDAS • FINANCEIRO • OPERAÇÃO GLOBAL</p></section>
<h3 class="pressure-title">⚡ PRESSÃO OPERACIONAL — TEMPO REAL</h3><section class="gauges">
<div class="gauge card" id="g-general"><b>WERO1 GERAL</b><div class="dial" id="dial-general"><i class="needle"></i></div><div class="dial-scale" id="scale-general"><span>0</span><span>500</span><span>1000</span></div><div class="pressure" id="p-general">—</div><span class="muted">eventos rastreados • escala dinâmica</span></div>
<div class="gauge card idle"><b>wero1-operario</b><div class="dial" id="dial-operario"><i class="needle"></i></div><div class="dial-scale" id="scale-operario"><span>0</span><span>500</span><span>1000</span></div><div class="pressure" id="p-operario">—</div><span class="muted">telemetria externa pendente</span></div>
<div class="gauge card idle"><b>wero1mercados</b><div class="dial" id="dial-mercados"><i class="needle"></i></div><div class="dial-scale" id="scale-mercados"><span>0</span><span>500</span><span>1000</span></div><div class="pressure" id="p-mercados">—</div><span class="muted" id="movement">aguardando eventos</span></div>
<div class="gauge card"><b>wero1ouro</b><div class="dial" id="dial-ouro"><i class="needle"></i></div><div class="dial-scale" id="scale-ouro"><span>0</span><span>500</span><span>1000</span></div><div class="pressure" id="p-ouro">—</div><span class="muted">aguardando integração</span></div>
<div class="gauge card"><b>wero1eletrico</b><div class="dial" id="dial-eletrico"><i class="needle"></i></div><div class="dial-scale" id="scale-eletrico"><span>0</span><span>500</span><span>1000</span></div><div class="pressure" id="p-eletrico">—</div><span class="muted">aguardando integração</span></div>
</section><section id="tab-panel" class="tab-panel card" hidden><h2 id="tab-title"></h2><p id="tab-description" class="muted"></p><div class="tab-metrics" id="tab-metrics"></div><p id="tab-links"></p></section><section class="kpis"><div class="kpi card">🤖 Robôs Online<b id="robots">—</b></div><div class="kpi card">🛒 Vendas Confirmadas<b id="sales">—</b></div><div class="kpi card">💲 Valor Confirmado<b id="gross">—</b></div><div class="kpi card">％ Comissões<b id="commission" class="pink">—</b></div><div class="kpi card">🏦 Saldo na Plataforma<b>—</b><span class="muted">Aguardando fonte</span></div><div class="kpi card">↔ Transferências<b>—</b><span class="muted">Aguardando fonte</span></div></section>
<div class="mainrow"><section class="chart card"><h3>🛒 Vendas e Comissões — dados confirmados</h3><p id="chart-message" class="muted">Aguardando dados comerciais confirmados.</p><p class="warning">Sem gráfico simulado. Os valores são informados pelo banco e pela integração comercial.</p></section><section class="card" style="padding:16px"><h3>📈 Previsão Financeira</h3><p class="muted">Indisponível até haver histórico suficiente de comissões confirmadas.</p><p class="warning">Nenhuma projeção artificial será exibida como receita ou saldo.</p></section></div>
<section class="robots"><div class="robot card"><h3>🤖 wero1 operário</h3><span class="muted">Integração independente</span><div class="social">♪ ◎ f ◉</div></div><div class="robot card"><h3>🛒 wero1mercados</h3><b class="green" id="marketstatus">Verificando…</b><p>Vendas: <span id="marketsales">—</span><br>Comissão: <span id="marketcommission">—</span></p><div class="social">♪ ◎ f ◉</div></div><div class="robot card"><h3>♛ wero1ouro</h3><span class="muted">Aguardando integração</span><div class="social">♪ ◎ f ◉</div></div><div class="robot card"><h3>⚡ wero1eletrico</h3><span class="muted">Aguardando integração</span><div class="social">♪ ◎ f ◉</div></div></section>
<section class="bottom"><div class="card"><h3>📦 Vendas por Produto</h3><p class="muted">Dados confirmados aparecerão aqui.</p></div><div class="card"><h3>🌐 Países / Top Mercado</h3><p>Brasil — mercado atual</p></div><div class="card"><h3>🌍 Operação Global</h3><p class="muted">Expansão conforme integrações reais.</p></div></section>
</main>
<aside class="right"><div class="card"><h3>💚 Status do Sistema</h3><div class="statusline"><span>Banco de Dados</span><b id="dbs">Verificando</b></div><div class="statusline"><span>Servidor</span><b id="server">Verificando</b></div><div class="statusline"><span>Dashboard</span><b class="green">Online</b></div></div><div class="card"><h3>🔔 Últimas Notificações</h3><div class="notice">Dashboard PARADIGMA iniciado</div><div class="notice">Aguardando vendas confirmadas</div></div><div class="card"><h3>☑ Próximas Ações</h3><div class="notice">Monitorar novas vendas</div><div class="notice">Acompanhar comissões</div><div class="notice">Integrar demais robôs</div></div></aside>
</div>
<script>

let snapshot={};
const tabTitles={dashboard:'Visão Geral',robots:'Robôs',sales:'Vendas Digitais',finance:'Financeiro',reports:'Relatórios',notifications:'Notificações',settings:'Configurações',help:'Ajuda e Suporte'};
const brlSafe=n=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(n||0));
function tabView(tab){
 if(!tabTitles[tab])tab='dashboard';
 document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-current',b.dataset.tab===tab?'page':'false'));
 const panel=document.getElementById('tab-panel');panel.hidden=tab==='dashboard';
 document.querySelectorAll('.hero,.pressure-title,.gauges,.kpis,.mainrow,.robots,.bottom').forEach(e=>e.hidden=tab!=='dashboard');
 if(tab==='dashboard')return;
 document.getElementById('tab-title').textContent=tabTitles[tab];
 document.getElementById('tab-description').textContent='Indicadores confirmados e integrações conhecidas. Dados atualizados a cada 15 segundos.';
 const C=snapshot.c||{},H=snapshot.h||{},ok=H.status==='ok'&&H.database_ok===true;
 const data={
 robots:[['wero1mercados',ok?'Online':'Não confirmado'],['wero1-operario','Telemetria externa pendente'],['wero1ouro','Integração pendente'],['wero1eletrico','Integração pendente']],
 sales:[['Ofertas ativas',C.active_offers],['Cliques internos',C.clicks],['Vendas confirmadas',C.confirmed_sales],['Valor confirmado',brlSafe(C.confirmed_sales_brl)]],
 finance:[['Valor confirmado',brlSafe(C.confirmed_sales_brl)],['Comissões confirmadas',brlSafe(C.confirmed_commission_brl)],['Saldo disponível','Fonte pendente'],['Transferências','Fonte pendente']],
 reports:[['Ofertas ativas',C.active_offers],['Cliques internos',C.clicks],['Vendas confirmadas',C.confirmed_sales],['Comissões',brlSafe(C.confirmed_commission_brl)]],
 notifications:[['Servidor',ok?'Saudável':'Não confirmado'],['Vendas',Number(C.confirmed_sales||0)?'Há conversões':'Aguardando confirmação']],
 settings:[['Versão',H.version],['Banco PostgreSQL',H.database_ok===true?'Conectado':'Não confirmado'],['Mercado',H.market]],
 help:[['Health',ok?'OK':'Não confirmado'],['Dados','Wero1 / PostgreSQL']]
 };
 const area=document.getElementById('tab-metrics');area.replaceChildren();
 (data[tab]||[]).forEach(([label,value])=>{const d=document.createElement('div'),a=document.createElement('span'),b=document.createElement('b');a.textContent=label;b.textContent=value===undefined?'—':String(value);d.append(a,b);area.append(d)});
 const links=document.getElementById('tab-links');links.replaceChildren();
 const urls=tab==='help'||tab==='settings'?[['Health','/health'],['Comercial','/api/commercial']]:tab==='sales'?[['Ofertas','/api/offers']]:tab==='reports'?[['Relatório comercial','/api/commercial']]:[];
 urls.forEach(([label,url],i)=>{if(i)links.append(' · ');const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener';a.textContent=label;links.append(a)});
}
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{location.hash=b.dataset.tab;tabView(b.dataset.tab);window.scrollTo(0,0)}));
window.addEventListener('hashchange',()=>tabView(location.hash.slice(1)));

let lastClicks=null,lastSales=null;
function setPressure(id,value){
 const d=document.getElementById('dial-'+id),p=document.getElementById('p-'+id),scale=document.getElementById('scale-'+id);
 if(value===null||!Number.isFinite(Number(value))){if(p)p.textContent='—';if(d)d.style.setProperty('--p',0);return;}
 const n=Math.max(0,Number(value));let max=1000;while(n>=max&&max<1073741824)max*=2;
 if(d)d.style.setProperty('--p',Math.max(0,Math.min(100,n/max*100)));
 if(p)p.textContent=new Intl.NumberFormat('pt-BR').format(n);
 if(scale){const labels=scale.querySelectorAll('span');[0,max/2,max].forEach((v,i)=>{if(labels[i])labels[i].textContent=new Intl.NumberFormat('pt-BR').format(v)});}
}
function pulseSale(){const g=document.getElementById('g-general');g.classList.remove('pulse');void g.offsetWidth;g.classList.add('pulse');}
const brl=n=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(n||0));
async function refresh(){
 try{
  const [h,c,p]=await Promise.all([fetch('/health'),fetch('/api/commercial'),fetch('/api/products?limit=500')]);
  const H=await h.json(), C=await c.json(), P=await p.json();
  snapshot={h:H,c:C};tabView(location.hash.slice(1)||'dashboard');
   const ok=H.status==='ok'&&H.database_ok===true;
  document.getElementById('dbs').textContent=ok?'Online':'Falha'; document.getElementById('dbs').className=ok?'green':'pink';
  document.getElementById('server').textContent=H.status==='ok'?'Online':'Falha'; document.getElementById('server').className=H.status==='ok'?'green':'pink';
  document.getElementById('marketstatus').textContent=ok?'Online':'Offline';
  const sales=Number(C.confirmed_sales||0), gross=Number(C.confirmed_sales_brl||0), comm=Number(C.confirmed_commission_brl||0), clicks=Number(C.clicks||0), offers=Number(C.active_offers||0);
  const clickDelta=lastClicks===null?0:Math.max(0,clicks-lastClicks), saleDelta=lastSales===null?0:Math.max(0,sales-lastSales);
  // Pressure is telemetry, not financial data: baseline only indicates a healthy running service.
  const pressure=ok?Math.min(100,Math.max(0,clickDelta*12 + saleDelta*15)):0;
  setPressure('mercados',pressure); setPressure('general',pressure);
  document.getElementById('movement').textContent=ok?('eventos registrados: '+clicks+' cliques / '+sales+' vendas confirmadas'):'telemetria indisponível';
  if(saleDelta>0)pulseSale(); lastClicks=clicks; lastSales=sales;
  document.getElementById('robots').textContent=ok?'1 confirmado':'0 confirmado';
  document.getElementById('sales').textContent=sales; document.getElementById('gross').textContent=brl(gross); document.getElementById('commission').textContent=brl(comm);
  document.getElementById('marketsales').textContent=sales; document.getElementById('marketcommission').textContent=brl(comm);
  document.getElementById('chart-message').textContent='Vendas confirmadas: '+sales+' | Valor: '+brl(gross)+' | Comissões: '+brl(comm);
 }catch(e){document.getElementById('server').textContent='Falha de leitura';}
}
tabView(location.hash.slice(1)||'dashboard');refresh(); setInterval(refresh,15000);
</script></body></html>"""

@app.get("/")
def root():
    return {
        "service": SERVICE,
        "version": VERSION,
        "status": WERO_MODE,
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
                       COUNT(po.id) FILTER (WHERE po.active=TRUE AND p.active=TRUE) AS active_offers,
                       MIN(po.price_brl) FILTER (WHERE po.active=TRUE AND p.active=TRUE) AS best_price_brl
                FROM products pr
                LEFT JOIN categories c ON c.id=pr.category_id
                LEFT JOIN offers po ON po.product_id=pr.id
                LEFT JOIN partners p ON p.id=po.partner_id
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
                              commission_brl=EXCLUDED.commission_brl,
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


@app.get("/go/{offer_id}", response_class=HTMLResponse)
def go_offer_landing(
    offer_id: int,
    channel: str = Query(default="direct", max_length=40),
    campaign: str = Query(default="", max_length=80),
):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id, o.title, o.authorized_url, o.active, p.name AS partner_name,
                       p.domain, p.active AS partner_active
                FROM offers o JOIN partners p ON p.id=o.partner_id
                WHERE o.id=%s
            """, (offer_id,))
            row = cur.fetchone()
    if not row or not row["active"] or not row["partner_active"]:
        raise HTTPException(status_code=404, detail="Oferta indisponivel")
    validate_authorized_url(row["authorized_url"], row["domain"])
    title = html.escape(row["title"])
    partner = html.escape(row["partner_name"])
    safe_query = html.escape(urlencode({"channel": channel, "campaign": campaign}), quote=True)
    return HTMLResponse(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title></head>
<body style="font-family:system-ui;max-width:680px;margin:40px auto;padding:0 20px;line-height:1.5">
<main><h1>{title}</h1>
<p>Oferta disponível em <strong>{partner}</strong>.</p>
<p><strong>Publicidade / link de associado.</strong> Esta oferta pode gerar comissão por compras qualificadas, conforme as regras do parceiro.</p>
<p>Ao tocar no botão abaixo, você será direcionado para o site do parceiro {partner}. Nenhum redirecionamento acontece automaticamente.</p>
<form method="post" action="/out/{offer_id}?{safe_query}">
<button type="submit" style="font-size:18px;padding:14px 20px;cursor:pointer">Ver oferta no parceiro</button>
</form></main></body></html>""")


@app.post("/out/{offer_id}")
def confirm_offer_click(
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
    return RedirectResponse(target, status_code=303)


class ProviderConversionIn(BaseModel):
    external_id: str = Field(min_length=1, max_length=200)
    offer_id: int = Field(gt=0)
    status: str = Field(min_length=1, max_length=40)
    sale_amount_brl: Decimal | None = Field(default=None, ge=0)
    commission_brl: Decimal | None = Field(default=None, ge=0)
    confirmed_at: datetime | None = None


@app.post("/api/commercial/conversions/provider")
def ingest_provider_conversion(
    payload: ProviderConversionIn,
    _admin: None = Depends(require_admin),
):
    """Ingest only data already confirmed/reported by an authorized partner source."""
    external_id = payload.external_id.strip()
    status = payload.status.strip().lower()
    allowed = {"pending", "confirmed", "reversed", "cancelled"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail="Status de conversao invalido")
    if status == "confirmed" and payload.confirmed_at is None:
        raise HTTPException(status_code=400, detail="Conversao confirmada exige confirmed_at")
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id
                FROM offers o JOIN partners p ON p.id=o.partner_id
                WHERE o.id=%s AND p.active=TRUE
            """, (payload.offer_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Oferta/parceiro nao encontrado")
            cur.execute("""
                INSERT INTO conversions(external_id,offer_id,status,sale_amount_brl,commission_brl,confirmed_at)
                VALUES(%s,%s,%s,%s,%s,%s)
                ON CONFLICT(external_id) DO UPDATE SET
                    offer_id=EXCLUDED.offer_id,
                    status=EXCLUDED.status,
                    sale_amount_brl=EXCLUDED.sale_amount_brl,
                    commission_brl=EXCLUDED.commission_brl,
                    confirmed_at=EXCLUDED.confirmed_at
                RETURNING id
            """, (
                external_id, payload.offer_id, status, payload.sale_amount_brl,
                payload.commission_brl, payload.confirmed_at,
            ))
            conversion_id = cur.fetchone()["id"]
    return {
        "status": "accepted",
        "conversion_id": conversion_id,
        "external_id": external_id,
        "provider_status": status,
        "financial_rule": "Somente dados recebidos de fonte parceira autorizada devem usar este endpoint.",
    }


@app.get("/api/acquisition")
def acquisition():
    """Diagnose the real commercial funnel and prioritize authorized offers without fabricating demand."""
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT o.id,o.title,o.price_brl,o.commission_brl,COUNT(c.id) AS clicks
                           FROM offers o LEFT JOIN clicks c ON c.offer_id=o.id
                           JOIN partners p ON p.id=o.partner_id
                           WHERE o.active=TRUE AND p.active=TRUE GROUP BY o.id
                           ORDER BY clicks DESC,o.commission_brl DESC NULLS LAST,o.id""")
            rows=cur.fetchall()
            cur.execute("SELECT COUNT(*) AS c FROM clicks"); clicks=cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM conversions WHERE status='confirmed'"); sales=cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM conversions WHERE status='pending'"); pending=cur.fetchone()["c"]
    if not rows: bottleneck,next_action="NO_ACTIVE_OFFERS","IMPORT_AUTHORIZED_OFFERS"
    elif clicks==0: bottleneck,next_action="NO_TRACKED_TRAFFIC","DISTRIBUTE_TRACKED_CAMPAIGNS"
    elif pending==0 and sales==0: bottleneck,next_action="NO_CONVERSION_SIGNAL","OPTIMIZE_OFFER_AND_LANDING"
    elif sales==0: bottleneck,next_action="PENDING_WITHOUT_CONFIRMED_SALE","VERIFY_PROVIDER_AND_OPTIMIZE_CONVERSION"
    else: bottleneck,next_action="FUNNEL_CONVERTING","SCALE_WINNERS"
    queue=[{"priority":n+1,"offer_id":r["id"],"title":r["title"],"tracked_clicks":r["clicks"],
            "tracked_url":f"/go/{r['id']}?channel=campaign&campaign=wero-acquisition",
            "objective":"FIRST_CONFIRMED_SALE" if sales==0 else "SCALE_CONFIRMED_SALES"}
           for n,r in enumerate(rows)]
    return {"engine":"wero-acquisition","service":SERVICE,"version":VERSION,"bottleneck":bottleneck,
            "next_action":next_action,"active_offers":len(rows),"tracked_clicks":clicks,
            "pending_conversions":pending,"confirmed_sales":sales,"campaign_queue":queue,
            "rule":"Somente conversoes reais confirmadas pela fonte parceira contam como vendas."}


@app.get("/api/commercial")
def commercial():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM offers o JOIN partners p ON p.id=o.partner_id WHERE o.active=TRUE AND p.active=TRUE")
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


@app.get("/api/catalog/levels")
def catalog_levels():
    """Operational catalog coverage. Counts inventory/offers only; never represents sales."""
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM products WHERE active=TRUE AND market='BR'")
            products = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM offers WHERE active=TRUE")
            offers = cur.fetchone()["c"]
            cur.execute("""SELECT p.name AS partner, COUNT(DISTINCT o.product_id) AS products, COUNT(o.id) AS offers
                           FROM partners p LEFT JOIN offers o ON o.partner_id=p.id AND o.active=TRUE
                           WHERE p.active=TRUE GROUP BY p.id,p.name ORDER BY offers DESC,p.name""")
            partners = cur.fetchall()
            cur.execute("""SELECT c.slug,c.name,COUNT(DISTINCT pr.id) AS products,COUNT(o.id) AS offers
                           FROM categories c LEFT JOIN products pr ON pr.category_id=c.id AND pr.active=TRUE
                           LEFT JOIN offers o ON o.product_id=pr.id AND o.active=TRUE
                           WHERE c.active=TRUE GROUP BY c.id,c.slug,c.name ORDER BY products DESC,c.name""")
            categories = cur.fetchall()
    if products >= 1000: level="L4_SCALE"
    elif products >= 100: level="L3_GROWTH"
    elif products >= 10: level="L2_CATALOG"
    elif products >= 1: level="L1_BOOTSTRAP"
    else: level="L0_EMPTY"
    return {"service":SERVICE,"version":VERSION,"market":"BR","catalog_level":level,
            "active_products":products,"active_offers":offers,"partners":partners,"categories":categories,
            "rule":"Nivel mede cobertura de catalogo/ofertas; nao representa vendas, receita ou comissao."}
