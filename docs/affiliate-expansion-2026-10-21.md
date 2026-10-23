# PARADIGMA — Expansão de afiliados (2026-10-21)

Status: planejamento, sem aprovação de contas nem deploy.

## Matriz de parceiros
- Mercado Livre: Mercados, Gammer, Elétrico; inscrição e autorização pendentes.
- Hotmart: Operário e produtos digitais; cadastro e HotLinks específicos pendentes.
- Kiwify: Operário; aprovação de afiliação por produto pendente.
- Eduzz: Operário; conta e produto pendentes.
- Leroy Merlin: Elétrico; elegibilidade do programa pendente.
- Awin: Gammer, Elétrico, Mercados; depósito de verificação e aprovação pendentes. Não contratar sem autorização explícita.

## Gates obrigatórios
1. Validar titularidade e aprovação de cada conta e produto, sem coletar senhas ou expor tokens.
2. Confirmar permissão de tráfego, publicidade, automação e uso de marca.
3. Registrar identificador, link de afiliado e origem por plataforma e robô.
4. Rejeitar links sem atribuição comprovável (fail closed).
5. Testar redirecionamentos em ambiente isolado sem cliques ou compras artificiais.
6. Conciliar venda e comissão somente com proveniência autenticada do parceiro.
7. Double Check, health, canary e rollback antes de qualquer deploy.

## Bloqueios P0
- Sem evidência de contas aprovadas nas novas plataformas.
- Sem links individuais de afiliado autorizados.
- Sem confirmação das integrações em código e do banco efetivo de produção.
- Sem reconciliação autenticada de comissões.

Não alterar produção, não cadastrar contas em nome do usuário, não pagar depósitos nem publicar ofertas sem autorização e validação.
