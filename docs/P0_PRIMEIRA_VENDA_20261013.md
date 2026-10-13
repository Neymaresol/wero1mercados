# PARADIGMA / Wero1Mercados — P0 primeira venda, correções de desenvolvimento

**Versão:** proposta em `dev/p0-first-sale-observability-20261013` — 2026-10-13 (America/Sao_Paulo).
**Estado:** desenvolvimento; NÃO implantada em produção. Sem migração, merge ou deploy.

## Evidências auditadas (somente leitura)

Fonte consultada: PostgreSQL Render `wero1mercados-db` (`dpg-db2h93h7lnhs73ev17og-a`), no mesmo ambiente de serviço Render do Wero1Mercados. O mapeamento exato do `DATABASE_URL` da aplicação não foi exposto pelas ferramentas; correspondência da configuração em runtime deve ser validada antes de um GO.

- Banco Render: 20 ofertas, **19 ativas**, 42 visitas a `/go/`, **42 registros de cliques**, 8 acessos ao catálogo, **0 registros em conversions**.
- Oferta 802: ativa, parceiro Amazon ativo, `tag=wero1mercados-20` presente; 22 visitas a ofertas e 5 registros de cliques (1 `facebook/lancamento-casa-jardim-1110`, 4 `social/werozinha-amazon`).
- Oferta 164: ativa, parceiro Amazon ativo, tag esperada presente; 9 visitas `facebook/moda-infantil-out26` e 6 registros de cliques históricos (4 `catalogo`, 2 `campaign/wero-acquisition`), **nenhum clique de saída atribuído à campanha Facebook**.
- Logs Render registram `POST /out/802` e `POST /out/164` com HTTP 303. Os registros não comprovam navegação subsequente, compra, nem usuário único.
- Publicações Facebook foram confirmadas via Metricool. Relatório Amazon autenticado não disponível; nenhuma venda/comissão pode ser dada como confirmada.

## Alterações preparadas

1. Endpoint **`GET /api/p0/funnel-audit`**, com token administrativo obrigatório, SQL `SET TRANSACTION READ ONLY`, sem chamadas HTTP externas, sem gravar visitas/cliques, relatando por oferta e por campanha contagens existentes e sinais de autorização Amazon.
2. Segregação dos cliques de um redirect GET `werozinha-amazon` como `UNVERIFIED_GET_REDIRECT`; esses registros podem incluir bots ou prefetch. Não somar como compradores humanos.
3. Diagnóstico do `DATABASE_URL` sem publicar host, senha, nome de DB ou URL. HMAC opcional apenas se `DB_DIAGNOSTIC_KEY` existir, tiver 32+ caracteres e for gerenciado como segredo; nenhum segredo novo é definido aqui.
4. Na landing `/go/{offer_id}`, CTA Amazon fica visível antes do painel de parceiro e explicita que preço/disponibilidade são verificados na Amazon. O clique continua somente via `POST /out/{offer_id}`.
5. Testes de agregação offline e de autenticação/transação read-only em PostgreSQL temporário do GitHub Actions. Não executar `/go/` nem `/out/` em produção para testar.

## P0 ainda não resolvido por código

- A conexão exata de runtime da produção deve ser comparada com a instância Render consultada sem expor credenciais. A presença do banco no workspace e a correspondência de eventos constituem evidência, mas não autenticam a variável de ambiente do serviço.
- **Conversões/comissões Amazon:** exige relatório autenticado do programa de associados e conciliação de pedidos/estornos com origem verificável; IDs de cliques internos isolados não identificam pedidos da Amazon.
- `affiliate_conversion_ledger` existente em staging não prova vendas em produção. **Não inserir vendas sintéticas**, não contabilizar conversões legadas como provas de parceiro.

## Double Check para revisão

- CI: `python -m unittest discover -s tests -p 'test_*.py' -v` + PostgreSQL temporário isolado.
- Sem token: `GET /api/p0/funnel-audit` deve negar acesso. Com token em staging: apenas SELECT, não deve alterar `clicks`, `offer_landing_visits` ou `conversions`.
- Comparar contagens e campanhas no endpoint com consultas SQL SELECT no banco de staging.
- Testar CTA e POST /out em **staging somente**, com destino de teste autorizado. Validar links afiliados de produção sem disparar cliques.
- Validar `/health`, `/api/offers`, `/api/commercial`, perfis de carga e rollback. GO somente após teste e autorização explícita.

**Rollback:** não há alteração de schema neste PR. Manter commit LIVE anterior na produção. Se o PR falhar, corrigir ou revertê-lo na branch; não alterar o banco nem reiniciar o serviço em produção.
