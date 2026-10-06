# wero1mercados

Robô do ecossistema PARADIGMA dedicado a vendas digitais de produtos físicos no mercado brasileiro.

## Status

🟡 v1.6.0-BR em validação para GO comercial de varejo físico.

## Escopo oficial

- produtos físicos vendidos por varejistas, marketplaces e parceiros autorizados
- Brasil / pt-BR / BRL
- categorias como eletrônicos, celulares, informática, casa, cozinha, eletrodomésticos, beleza, moda, ferramentas, automotivo, esportes e pet
- não replica o catálogo de cursos/e-books do wero1 operário
- links de destino precisam ser HTTPS e pertencer ao domínio autorizado do parceiro
- nenhuma parceria, preço, comissão ou venda é inventada

## Fluxo comercial

Parceiro autorizado -> produto -> oferta -> /go/{offer_id} -> clique rastreado -> loja parceira -> conversão confirmada pelo parceiro -> dashboard.

## Controles

- cadastro de produtos e ofertas protegido por Bearer admin token
- produto idempotente por SKU
- oferta idempotente por produto + parceiro + URL autorizada
- preço e comissão comerciais não contam como venda
- vendas e comissões entram nos totais somente após conversão confirmada pela fonte parceira
- implantação por Double Check, health check e canary
- rollback preservado pela versão anterior em produção

Última versão preparada: 2026-10-06 (UTC).
