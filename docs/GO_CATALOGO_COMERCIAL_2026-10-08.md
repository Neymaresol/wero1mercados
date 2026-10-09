# GO comercial — catálogo autorizado (08/10/2026)

## Estado confirmado
- Produção: wero1mercados v1.14.0-BR; health PostgreSQL OK.
- Última consulta comercial fornecida: 1 oferta ativa, 2 cliques, 0 vendas e R$ 0,00 em comissões confirmadas.
- Operário v1.9.0: 4 ofertas ativas, 0 cliques, 0 vendas; Amazon Creators API aguardando credenciais.

## Procedimento seguro para abrir catálogo
1. Consultar GET /health, /api/catalog/levels, /api/products e /api/offers. Guardar contagens e IDs como baseline.
2. Confirmar autorização comercial do parceiro e URL de afiliação válida; não importar produtos sem autorização, preço ou comissão inventados.
3. Cadastrar produtos ativos pelo POST /api/commercial/products usando credencial administrativa existente; depois vincular cada produto ao parceiro com POST /api/commercial/offers. Nunca publicar token ou credenciais no repositório/logs.
4. Verificar GET /api/offers e /api/catalog/levels. Exigir incremento esperado de ofertas e consistência de SKU, domínio, URL, produto e parceiro.
5. Validar landing GET /go/{offer_id}?channel=organic&campaign=catalog-go sem registrar cliques artificiais. O clique só deve ser contabilizado quando o visitante escolher continuar para a loja.
6. Publicar ofertas apenas em canais conectados e autorizados. Registrar campanha, canal e IDs; respeitar regras de cada marketplace.
7. Verificar GET /api/commercial e /api/acquisition. Distinguir cliques reais, testes e vendas; registrar vendas e comissões somente após conversão autenticada pela fonte parceira.
8. Acompanhar o dashboard PARADIGMA com versão, horário, health, ofertas, cliques, vendas e comissões. Double Check antes de merge/deploy; preservar rollback.

## Critérios de GO
- Health e DB OK; links autorizados; catálogo com produtos reais; fluxo de clique rastreável; conversões validadas; monitoramento ativo.
- Amazon: Partner Tag não substitui credenciais Creators API. Não usar resultados de catálogo fabricados.
- Nunca automatizar publicação em contas sem permissão nem tratar requisições de teste como vendas.

## Pendências externas
- Credenciais Amazon Creators API e aprovação de outros programas de afiliados, quando aplicável.
- Conexões autorizadas dos canais de distribuição e verificação de tráfego real.
