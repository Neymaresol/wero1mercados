# wero1mercados

Robô PAI do ecossistema PARADIGMA dedicado ao mercado brasileiro.

## Status

🟡 Camada comercial em validação — v1.4.0-BR

## Objetivo

Operar ofertas e links de afiliados autorizados no Brasil, com rastreabilidade de cliques, vendas e comissões confirmadas sem inventar resultados financeiros.

## Princípios

- Brasil / pt-BR / BRL
- parceiros e links autorizados
- vendas e comissões somente após confirmação da fonte
- separação total do WERO1 Operário
- integração futura ao PARADIGMA como robô PAI
- implantação por testes, Double Check, health check e canary

## Camada comercial v1.4.0-BR

- cadastro de ofertas comerciais protegido por Bearer admin token
- oferta vinculada a produto e parceiro autorizado
- URL HTTPS validada contra o domínio do parceiro
- clique rastreado pelo endpoint /go/{offer_id}
- preço e comissão da oferta são metadados comerciais; somente conversões confirmadas entram nos totais financeiros
- nenhuma oferta real é criada automaticamente sem dados autorizados da fonte parceira

Última versão preparada: 2026-10-06 (UTC).
