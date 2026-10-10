# Wero1Elétrico — Protótipo v1.0.0-BR
Data da versão: 2026-10-10 (horário não verificado).
Mercado: carros 100% elétricos, híbridos plug-in e híbridos convencionais, novos e seminovos no Brasil.

## Objetivo
Espelhar a arquitetura de funil do Wero1Mercados, adaptando o negócio para captação consentida de leads e fechamento por concessionárias parceiras. Não há afiliação automática de fabricantes nem inventário real sem contrato.

## Rodar isoladamente
Na raiz do repositório: `uvicorn wero1eletrico.main:app --port 8081`
Requer FastAPI, Pydantic e Uvicorn. Endpoint GET /health, GET /api/catalog, POST /api/leads e GET /api/commercial.

## Limites do protótipo
SQLite temporário APENAS para análise local; não usar em produção. Nenhum nome, telefone ou email é coletado nesta etapa. Falta autenticação, antispam, rate limit, banco PostgreSQL isolado, parceiros, estoque, contratos, política LGPD, confirmação de vendas e integração ao PARADIGMA. Indicadores financeiros nunca são simulados.

## GO
1. Revisar fluxo de consentimento, retenção e privacidade.
2. Conectar PostgreSQL próprio e autenticação.
3. Integrar parceiros e catálogo autorizado.
4. Testar em staging, com health checks e rollback.
5. Criar serviço Render independente, sem tocar Wero1Mercados/Operário.
