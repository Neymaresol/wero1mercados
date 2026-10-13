# Especificação funcional — Wero1Mercados / PARADIGMA
**ID:** EF-W1M-001 | **Versão:** 1.0 | **Última atualização:** 13/10/2026 19:37 BRT (UTC-03)
**Estado:** diretriz de desenvolvimento; automação integral ainda não validada.
**Escopo:** Wero1Mercados, Wero1Divulgação, Werozinha, TAG 1 e TAG 2. Wero1Ouro e Wero1Elétrico fora de escopo.

## Objetivo
Detectar interesse público/agregado → selecionar ofertas de afiliado reais e autorizadas → divulgar organicamente em canais permitidos → registrar visitas e cliques → redirecionar voluntariamente à loja parceira → conciliar venda autenticada → aprovar comissão com evidência do parceiro → acompanhar pagamento confirmado ao titular → otimizar e repetir continuamente.

## Gatilhos
- **INT.1 / TAG 1:** interesse agregado de busca (exemplo: banana), via Google Trends, Search Console próprio ou outras fontes autorizadas. Não permite identificar consultas privadas de pessoas no Google ou ChatGPT.
- **INT.2 / TAG 2:** tendências públicas e sinais autorizados de redes/influenciadores (exemplo: batom promovido por criador com alcance hipotético de um milhão). Não autoriza acesso aos dados privados dos seguidores.
- As duas TAGs classificam oportunidades e priorizam ofertas reais; nenhuma delas garante exibição a uma pessoa específica.

## Caminho feliz
1. Detectar e registrar sinal com fonte, data, tipo INT.1/INT.2 e confiança.
2. Cruzar demanda com catálogo efetivo e **bloquear** ofertas não ativas, não aprovadas ou sem autorização de afiliado.
3. Gerar campanha com campaign_id, task_id, offer_id, channel e strategy; controlar duplicação/frequência.
4. Publicar apenas por integração orgânica autorizada e registrar ID/URL de publicação comprovada.
5. Visitante escolhe clicar; Wero1Mercados registra visita e clique separadamente.
6. /go/{offer_id} valida oferta e redireciona para link afiliado autorizado.
7. Loja parceira realiza checkout; robô não processa nem inventa venda.
8. Conciliador verifica evento/relatório autenticado, idempotência, proveniência, cancelamento e estorno.
9. Comissão percorre estados estimada → pendente → aprovada/rejeitada/estornada → paga.
10. Pagamento ao criador só é confirmado após evidência do provedor; transferência automática depende de integração financeira e autorização próprias.
11. IA avalia dados reais, reajusta prioridades e repete o ciclo com recuperação de falhas.

## Exemplo fictício do simulador
Pedido R$100,00 × comissão **hipotética** 5% = R$5,00. Todos os eventos simulados são segregados; **0 vendas reais e 0 transferências reais**.

## Prioridades e execução
🔴 **P0/Alta:** health, banco efetivo, catálogo, links, autorização de ofertas, rastreamento, conciliação e segurança.
🟠 **P1/Média:** fontes de INT.1/INT.2, publicação orgânica, atribuição e otimização.
🟢 **P2/Baixa:** identidade visual, conteúdo e expansão pai-filhos 1→10→100→1000 após validação.
Ciclo: detectar → classificar → corrigir/planejar → testar → validar → medir → reclassificar → repetir. Rotina de acompanhamento **horária** configurada; worker contínuo 24/7 ainda exige implementação e testes. Retries idempotentes, backoff, circuit breaker, auditoria, health e rollback obrigatórios.

## Critérios de aceite
- Banco de produção identificado; persistência SQLite/Neon e catálogo validados.
- Ofertas reais aprovadas, /go/ rastreável e redirecionamento correto.
- Sinais INT.1/INT.2 provenientes de fontes públicas/autorizadas com data e proveniência.
- Publicações confirmadas por ID/URL da plataforma, sem custos pagos não autorizados.
- Visitas/cliques persistidos sem contarem como vendas.
- Vendas, comissões e pagamentos exibidos como confirmados somente com comprovação autenticada de parceiro/provedor.
- Staging isolado, testes, Double Check, canary, rollback e produção protegida.
- Dashboard com versão/data/hora/health no topo, status por robô e finanças confirmadas separadas de simulações.

## Estado técnico conhecido em 13/10/2026
Wero1Divulgação v0.3.0-dev confirmado live em staging (dep-db7ao9tg1s2s739q1v50). v0.4.0-dev e simulador INT.1/INT.2 enviados ao GitHub, deploy dep-db7b4nks728c73frj78g iniciado, ainda não comprovado live neste registro. Ingestão real de tendências, publicação automática contínua e conciliação financeira ponta a ponta ainda **não comprovadas**. Não confundir simulação com operação.

**Governança:** toda nova versão deve atualizar data/hora BRT, commit, deploy, testes, evidências, GAPs e rollback. Nenhum anúncio pago ou gasto novo sem autorização específica.
