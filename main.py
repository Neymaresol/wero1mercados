from datetime import datetime, timezone
from fastapi import FastAPI

VERSION = "1.0.0-BR"
SERVICE = "wero1mercados"

app = FastAPI(title="wero1mercados", version=VERSION)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": SERVICE,
        "version": VERSION,
        "market": "BR",
        "currency": "BRL",
        "time": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/")
def root():
    return {
        "service": SERVICE,
        "version": VERSION,
        "status": "development",
        "message": "wero1mercados Brasil",
    }
