# Qualidade de dados

## Como funciona

`dbt build` executa modelos e testes na ordem do grafo. Se um teste de severidade `error` falha, os modelos que dependem dele são **pulados** e o comando termina com código ≠ 0 (o DAG do Airflow e o CI falham junto). Testes que refletem anomalias conhecidas da origem usam `warn_if`/`error_if`: avisam enquanto o volume é o esperado e **falham se piorar**.

## Testes existentes

Execução de 2026-10-08, dataset real completo: **120 testes, 31 modelos, 145 PASS, 6 WARN, 0 ERROR** (≈6 s). No dataset sintético: 151/151 PASS.

| Tipo | Quantidade | Exemplos |
|---|---|---|
| Genéricos dbt (inclui os próprios) | 105 | `unique`, `not_null`, `relationships` (pedido→cliente, item→pedido/produto/vendedor, fatos→dimensões), `accepted_values` (status do pedido, tipo de pagamento, nota 1-5, faixas de atraso) |
| Genéricos próprios (parte dos 105) | — | `non_negative` (preço, frete, pagamento, peso), `positive` (`order_item_id`), `unique_combination` (chaves compostas e grão dos marts) |
| Singulares de negócio | 9 | entrega ≥ compra; aprovação ≥ compra; envio ≥ compra; entrega ≥ envio; envio vs. aprovação (monitorado); pedido entregue tem data de entrega; cancelado não tem entrega; `order_item_id` sequencial 1..N sem lacunas por pedido; pagamentos coerentes com o pedido |
| Singulares de reconciliação | 6 | contagem de pedidos raw = fct; soma de preço e frete e nº de itens iguais em raw, `fct_order_items`, `fct_orders` e `mart_sales_daily` (sem multiplicação por join); pagamentos raw = fct; avaliações raw = fct e pedidos avaliados iguais; cancelados não contam como entregues/receita nos marts; nenhum pedido some do mart de vendas |
| Python (pytest) | 19 passam + 1 (DAG) pulado sem Airflow instalado | validação de arquivos, checksum, colunas ausentes, arquivo vazio/ausente, BOM, campos multilinha, configuração e erro de conexão, **idempotência da carga** (integração, schema isolado `raw_test`), falha com rollback e registro, CLI, integridade do DAG |

Observação: a transformação de datas e a normalização de nulos são feitas no dbt (staging), não em Python; por isso são cobertas por testes dbt (`not_null`, tipos, ordem temporal) e não por pytest.

## Problemas encontrados nos dados originais

| Achado | Volume | Tratamento |
|---|---|---|
| `review_id` repetido entre pedidos diferentes | 814 | chave sintética `review_id + order_id` (sem duplicata nesse par) |
| Pedidos com mais de uma avaliação | 547 | usa-se a mais recente |
| Pedido `delivered` sem data de entrega | 8 | **WARN**; fora do denominador de atraso; falha se > 50 |
| Pedido `canceled` com data de entrega ao cliente | 6 | **WARN**; continua cancelado (nunca entregue); falha se > 50 |
| Envio à transportadora **antes da compra** | 166 | **WARN**; duração `NULL` e fora das médias; falha se > 500 |
| Entrega ao cliente **antes** do envio à transportadora | 23 | **WARN**; duração `NULL`; falha se > 500 |
| Envio antes da aprovação do pagamento | 1.359 | **WARN**; monitorado; despacho é medido desde a compra, então não distorce; falha se > 3.000 |
| Pagamentos divergem de produtos + frete (> R$ 1,00) | 249 | **WARN**; plausivelmente juros de parcelamento e vouchers (não investigado caso a caso); falha se > 500 |
| Pedidos sem itens | 775 | esperado (cancelados/indisponíveis/em criação); entram nos fatos com valor 0 |
| Pedido sem pagamento | 1 | mantido; `payments_total` nulo |
| Pagamentos com valor 0 / tipo `not_defined` | 9 / 3 | mantidos |
| Produtos sem categoria | 610 | categoria `unknown` |
| Categorias sem tradução | 2 | nome em português |
| CEP de cliente sem geolocalização | 278 clientes (1.265 pedidos sem distância) | faixa `unknown`, fora da análise de frete × distância |
| CEP de vendedor sem geolocalização | 7 | idem |
| Arquivo de tradução com BOM UTF-8 | 1 | lido com `utf-8-sig` |
| Nomes de coluna com erro (`lenght`) | 2 | renomeadas no staging |

Reconciliação (todos passaram): 99.441 pedidos em raw e `fct_orders`; 112.650 itens, soma de preço e frete idênticas em raw, `fct_order_items`, `fct_orders` e `mart_sales_daily`; 103.886 pagamentos; 99.224 avaliações.

## Limitações

- Não é possível verificar a corretude de preços, datas e notas além da consistência interna.
- Sem quantidade por item, sem custo de produto, portanto não há margem.
- Distâncias aproximadas (centróide por prefixo de CEP, coordenadas fora do Brasil descartadas).
- Os limiares `warn_if`/`error_if` foram definidos a partir desta execução; não são padrões da indústria.
- O CI valida o código em dados sintéticos; estes números vêm de uma execução local.
