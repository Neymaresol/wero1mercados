"""P0 Shopee: regressão do caminho cliente sem gravar eventos em GET.

Inspeciona a ordem das operações: GET /go é somente leitura; POST /out exige
um token válido antes de registrar clique, e oferta/parceiro inativo é rejeitado.
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


def test_go_rejects_inactive_before_token_issue_and_never_writes():
    src = _function_source("go_offer_landing")
    assert 'not row["active"]' in src
    assert 'not row["partner_active"]' in src
    assert src.index("raise HTTPException(status_code=404") < src.index(
        "issue_outbound_action_token("
    )
    assert "INSERT INTO offer_landing_visits" not in src
    assert "INSERT INTO clicks" not in src


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
