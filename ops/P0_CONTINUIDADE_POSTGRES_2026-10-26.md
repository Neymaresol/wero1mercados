# PARADIGMA — P0 continuidade PostgreSQL e gates de release
**Registro:** 2026-10-26 07:18 BRT (America/Sao_Paulo)
**Escopo:** Wero1Mercados / Wero1Divulgação. Documento operacional; **não executa** backup, migração, gasto, publicação ou deploy.

## Evidência consultada nesta iteração
- Render Postgres de produção: `dpg-db2h93h7lnhs73ev17og-a`, banco `wero1mercados`, PostgreSQL 18.6, status `available`, plano `free`.
- Expiração informada pela API: **2026-11-05 15:32:30 UTC = 2026-11-05 12:32:30 BRT**. Risco P0; nenhum upgrade pago autorizado.
- SQL **somente leitura** diretamente no banco Render: 11 tabelas públicas, 20 ofertas, 19 ativas, 82 cliques totais, 9 em sete dias, 0 em 24h, 44 visitas de landing, 8 visitas de catálogo, 0 conversões.
- Neon `wero1mercados-staging`: PostgreSQL 17.11, 13 tabelas (inclui `affiliate_conversion_audit` e `affiliate_conversion_ledger`), não equivale à produção Render.
- Neon `wero1mercados-production`: 0 tabelas públicas; o nome do projeto **não** comprova que seja o banco efetivo da aplicação.
- Consulta SQL direta comprova conectividade e leitura, **não** identidade da conexão em uso pelo processo web, durabilidade, backup recuperável ou health HTTP.
- Sem homologação HTTP isolada de `/go/{offer_id}` e `POST /out/{offer_id}`.

## Gates obrigatórios antes de qualquer alteração em produção
1. **Identidade:** com acesso autorizado ao serviço Render, confrontar `DATABASE_URL` do processo em execução com host, banco e instância esperados **sem expor credenciais**. Verificar variáveis `EXPECTED_DATABASE_NAME` e `EXPECTED_DATABASE_HOST` separadas por ambiente. O preflight da PR #106 é somente uma barreira, não prova identidade física.
2. **Continuidade:** estabelecer um backup consistente **autorizado**, testar restauração em destino isolado e confirmar contagens, integridade, esquema, sequência e dados com consulta somente leitura. Registrar horário, tamanho, resultado e responsável. Não declarar `backup_restored=true` sem restauração verificada.
3. **Compatibilidade:** a origem usa PG18 e o staging Neon usa PG17. **Não presumir** compatibilidade de downgrade físico ou de `pg_dump`/restore sem validação real de extensões, tipos, collation, objetos e versão do utilitário. Não sobrescrever banco existente.
4. **Health:** `/health` com `SELECT 1` mede apenas conectividade. A PR #108 retorna `storage_persistent=null`; com o gate atual, `/ready` responde **503 mesmo com DB acessível**, intencionalmente. **Não** apontar `healthCheckPath` do Render para `/ready` antes de projetar e homologar um critério operacional válido que não confunda conectividade com restore comprovado.
5. **Funil:** validar rotas em staging **isolado** com mocks/offline, sem chamar links reais de afiliado e sem registrar cliques ou vendas em produção. GET `/go/` pode registrar visitas não autenticadas; POST `/out/` representa tentativa de saída, **não** compra. Exigir autorização de parceiro e link válido.
6. **Conversões:** manter ingestão manual legada fechada. Uma conversão real requer origem autenticada do parceiro, verificação de assinatura ou credencial oficial, associação oferta/parceiro, idempotência, proteção a replay, estados reconciliados e auditoria; parâmetros `channel` e `campaign` são rótulos não autenticados.
7. **Ranking:** PR #104 deixa INT.1/INT.2 **bloqueado** sem evidência autenticada, mesmo quando há cliques recentes; PR #36 exige sinais consultivos positivos em ambas as fontes, mas isso **não** autentica intenção nem autoriza publicação.
8. **Release/rollback:** somente depois de CI no commit final, testes integrados em staging, backup restaurado, validação de schema, rollback demonstrado, health apropriado e revisão de mudanças. Manter `main` e produção intactos até Double Check completo. O merge em `main` pode disparar auto-deploy.

## Bloqueios atuais
- Falta comprovar health HTTP e conexão do **processo web** ao banco esperado.
- Falta backup **restaurável**, plano de continuidade antes da expiração e rollback ensaiado.
- Faltam testes HTTP integrados em staging e alinhamento de schemas PG18/PG17.
- Proveniência de conversões de parceiros ainda não autenticada ponta a ponta.
- PRs P0 #104, #106, #107, #108 e PR #36 Divulgação seguem sem deploy de produção.

## Restrições permanentes
Sem gastos, anúncios pagos, publicações automáticas, vendas ou cliques sintéticos; sem alterar Wero1Operário/Wero1Elétrico; sem contornar restrições de workspace ou acesso. Valores de staging e estimativas não são pagamentos comprovados.
