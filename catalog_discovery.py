"""Descoberta incremental de produtos de feeds oficiais de parceiros.

Este módulo NÃO faz scraping nem publica ofertas automaticamente.
O conector autorizado fornece páginas de produtos; o operador aprova a publicação.
"""
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Iterable, Mapping, Callable
import hashlib

@dataclass(frozen=True)
class Candidate:
    partner: str
    sku: str
    title: str
    url: str
    fingerprint: str

def normalize_candidate(raw: Mapping, partner: str, allowed_hosts: set[str]) -> Candidate:
    sku = str(raw.get("sku") or "").strip()
    title = str(raw.get("title") or "").strip()
    url = str(raw.get("affiliate_url") or "").strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not sku or not title or parsed.scheme != "https" or host not in allowed_hosts:
        raise ValueError("Produto incompleto ou URL fora da lista autorizada")
    fingerprint = hashlib.sha256(f"{partner}:{sku}".encode()).hexdigest()
    return Candidate(partner, sku, title, url, fingerprint)

def discover(fetch_page: Callable[[str | None], Mapping],
             partner: str, allowed_hosts: set[str], max_pages: int = 10):
    """Retorna candidatos e métricas, sem gravar nem ativar ofertas.

    fetch_page(cursor) deve devolver {'items': [...], 'next_cursor': str|None}.
    """
    if not 1 <= max_pages <= 100:
        raise ValueError("max_pages fora dos limites")
    seen_ids, seen_cursors = set(), set()
    cursor = None
    candidates = []
    rejected = 0
    pages = 0
    for _ in range(max_pages):
        page = fetch_page(cursor)
        pages += 1
        for item in page.get("items", []):
            try:
                candidate = normalize_candidate(item, partner, allowed_hosts)
            except (ValueError, AttributeError, TypeError):
                rejected += 1
                continue
            if candidate.fingerprint not in seen_ids:
                candidates.append(candidate)
                seen_ids.add(candidate.fingerprint)
        next_cursor = page.get("next_cursor")
        if not next_cursor or next_cursor in seen_cursors:
            break
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    return {"candidates": candidates, "pages": pages,
            "rejected": rejected, "unique_candidates": len(candidates),
            "publication_enabled": False}
