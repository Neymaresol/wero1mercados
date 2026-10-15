"""P0 Shopee: regressão do caminho cliente sem gravar cliques ou vendas.

Inspeciona a ordem das operações do código em produção: uma oferta/parceiro
inativo deve ser rejeitado antes de INSERT em ambas as rotas.
"""
import ast
from pathlib import Path


def _function_source(name: str) -> str:
    source = Path("main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name
    )
    return ast.get_source_segment(source, fn)


def test_go_rejects_inactive_before_visit_insert():
    src = _function_source("go_offer_landing")
    assert 'not row["active"]' in src
    assert 'not row["partner_active"]' in src
    assert src.index("raise HTTPException(status_code=404") < src.index(
        "INSERT INTO offer_landing_visits"
    )


def test_out_rejects_inactive_before_click_insert():
    src = _function_source("confirm_offer_click")
    assert 'not row["active"]' in src
    assert 'not row["partner_active"]' in src
    assert src.index("raise HTTPException(status_code=404") < src.index(
        "INSERT INTO clicks"
    )


def test_redirect_preserves_authorized_destination():
    src = _function_source("confirm_offer_click")
    assert 'validate_authorized_url(row["authorized_url"], row["domain"])' in src
    assert 'target = row["authorized_url"]' in src
    assert "RedirectResponse(target, status_code=303)" in src
