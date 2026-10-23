# PARADIGMA — Matriz de integração de afiliados
Data: 2026-10-21 (horário de execução não registrado)
Status: especificação técnica para desenvolvimento; **nenhuma plataforma ativada**.

| Provedor | Robôs | Inscrição | Link de produção |
|---|---|---|---|
| Mercado Livre | Mercados, Gammer, Elétrico | Pendente | Bloqueado |
| Hotmart | Operário (produtos digitais) | Pendente | Bloqueado |
| Kiwify | Operário | Pendente | Bloqueado |
| Eduzz | Operário | Pendente | Bloqueado |
| Leroy Merlin | Elétrico | Pendente | Bloqueado |
| Awin | Gammer, Elétrico, Mercados | Pendente (verificar depósito) | Bloqueado |

## Modelo proposto
partner_id, robot_id, program_status (unknown|pending|approved|suspended), approved_categories, destination_domains, tracking_template, tracking_id_reference, terms_reviewed_at, last_verified_at, source_evidence. Nunca armazenar segredos no Git.

## Validação antes de qualquer publicação
- Conta aprovada pelo parceiro e produto elegível; verificar restrições de canal e de anúncios.
- Link original fornecido pela plataforma e atribuição comprovável; não fabricar parâmetros ou encurtadores.
- HTTPS, domínio allowlisted, proteção contra open redirect e bloqueio fail-closed.
- Registro de clique apenas em acesso humano real; sem simular tráfego ou compra.
- Comissão marcada confirmed apenas mediante comprovante autenticado da plataforma; separar pending, rejected e confirmed.
- Banco de staging isolado, testes de integração, health, canary e rollback.

## Ordem de trabalho
1. Usuário conclui cadastros e aceita termos nos sites oficiais.
2. Coletar apenas IDs públicos, URLs de afiliação e evidência de aprovação; nunca senhas, CPF ou tokens no repositório.
3. Implementar conectores atrás de feature flags desativadas em branch de desenvolvimento.
4. Validar em staging e abrir PR de código para revisão; sem merge/deploy automático.

## Referências oficiais
- https://www.mercadolivre.com.br/l/afiliados-home
- https://www.mercadolivre.com.br/l/checklist
- https://hotmart.com/pt-br/afiliados
- https://help.hotmart.com/pt-BR/article/208424898/i-want-to-become-an-affiliate-what-do-i-need-to-know-to-get-started
