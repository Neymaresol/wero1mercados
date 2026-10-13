# Wero1Mercados — Double Check isolado (13/10/2026)

## Execução verificada
- Workflow: `.github/workflows/p0-isolated-postgres.yml` no PR #69.
- GitHub Actions run 38406266229: sucesso, incluindo inicialização do PostgreSQL 16 temporário, testes de proveniência e integração HTTP/PostgreSQL, e encerramento do contêiner.
- `DATABASE_URL` e `P0_TEST_DATABASE_URL` no workflow apontam somente para `localhost:5432/p0test`.
- O banco temporário do CI não é um staging persistente online e não substitui a validação da configuração do serviço Render.

## Critérios de segurança
1. Nunca inserir segredos de produção no job de testes; não configurar `DATABASE_URL` de produção em Actions.
2. Manter a validação de localhost no teste de integração.
3. Não usar banco Render de produção para homologação.
4. Confirmar testes de proveniência, redirecionamento, idempotência e rollback antes de promover versão.
5. Não fazer merge nem deploy em produção com esta documentação.

## Próxima etapa
Alinhar a branch de staging com o PR #69 somente após resolver divergências; manter deploy de staging bloqueado até comprovar banco isolado persistente ou modo offline sem escrita.
