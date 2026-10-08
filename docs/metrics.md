# Métricas e regras de negócio

Todas as regras vivem em SQL versionado (`dbt_project/models/intermediate/`) e são exercitadas por testes. Valores abaixo vêm da execução de 2026-10-08 sobre o dataset completo.

## Definições

| Conceito | Definição | Onde |
|---|---|---|
| Pedido entregue | `order_status = 'delivered'` | `is_delivered` |
| Pedido cancelado | `order_status = 'canceled'` (exclusivo de entregue; teste `assert_no_order_both_cancelled_and_delivered`) | `is_cancelled` |
| Pedido indisponível | `order_status = 'unavailable'` | `is_unavailable` |
| Pedido de receita | status fora de `canceled` e `unavailable` | `is_revenue_order` |
| Receita de produtos | soma de `price` dos itens de pedidos de receita. **Não inclui frete.** | `products_revenue` |
| Receita de frete | soma de `freight_value` dos itens de pedidos de receita | `freight_revenue` |
| Ticket médio | receita de produtos ÷ pedidos de receita *(só pedidos com itens somam receita)* | `avg_ticket` |
| Atraso | pedido **entregue, com data de entrega**, cuja **data** de entrega é posterior à **data** estimada | `is_delayed`, `days_late` |
| Taxa de atraso | pedidos atrasados ÷ pedidos entregues com data de entrega | |
| Taxa de entrega | pedidos entregues ÷ todos os pedidos | |
| Pedido não entregue | **nunca** conta como atraso (faixa `not_delivered`) | `delay_bucket` |
| Avaliação do pedido | nota **mais recente** (547 pedidos têm várias); pertence ao pedido, não ao produto | `review_score` |
| Avaliação baixa | nota ≤ 2 (`var low_review_max`) | `is_low_review` |
| Faixas de atraso | `on_time`, `late_1_3d`, `late_4_7d`, `late_8d_plus`, `not_delivered` | `delay_bucket` |
| Despacho | compra → entrega à transportadora, em dias | `days_purchase_to_carrier` |
| Etapas | compra→aprovação, aprovação→transportadora, transportadora→cliente, compra→entrega (dias, 2 casas) | `days_*` |
| Distância | haversine entre centróides de CEP de cliente e vendedor; no pedido, média dos itens | `distance_km`, `avg_distance_km` |
| Faixa de distância | `0-99`, `100-499`, `500-999`, `1000-1999`, `2000+ km`, `unknown` | `distance_bucket` |

Regras adicionais:
- Duração com ordem temporal impossível (ex.: envio antes da compra) vira `NULL` e fica fora das médias; o timestamp bruto permanece nos fatos.
- Um pedido pode ter vários itens e vendedores. Métricas de vendedor atribuem a cada vendedor o valor dos **seus** itens; a nota e o atraso do pedido são atribuídos a **todos** os vendedores dele.
- Notas de categoria usam a nota do pedido replicada em cada item (uma categoria "herda" notas causadas por itens de outras categorias do mesmo pedido).

## Resultados da execução real (todo o período)

| Indicador | Valor |
|---|---|
| Pedidos | 99.441 (compras de 2016-09-04 a 2018-10-17) |
| Receita de produtos (sem cancelados/indisponíveis) | R$ 13.494.401 |
| Receita de frete | R$ 2.241.126 |
| Ticket médio | R$ 137,41 |
| Entregues | 97,02% |
| Cancelados | 0,63% |
| Taxa de atraso | 6,77% |
| Nota média | 4,09 |
| Prazo médio de entrega | 12,6 dias (compra→aprovação 0,43; compra→transportadora 3,24; transportadora→cliente 9,33) |

| Situação de entrega | Pedidos avaliados | Nota média |
|---|---|---|
| No prazo | 89.443 | 4,29 |
| Atraso 1-3 dias | 1.852 | 3,29 |
| Atraso 4-7 dias | 1.748 | 2,10 |
| Atraso 8+ dias | 2.781 | 1,70 |
| Não entregue | 2.849 | 1,75 |

| Distância cliente-vendedor | Pedidos | Frete médio | Dias até entrega | Nota |
|---|---|---|---|---|
| 0-99 km | 18.267 | R$ 13,37 | 6,5 | 4,22 |
| 100-499 km | 37.877 | R$ 21,11 | 11,5 | 4,13 |
| 500-999 km | 26.289 | R$ 24,23 | 14,3 | 4,07 |
| 1000-1999 km | 9.958 | R$ 33,05 | 18,0 | 4,01 |
| 2000+ km | 5.785 | R$ 39,81 | 21,2 | 3,91 |

> Atraso e nota baixa caminham juntos, mas isto é **correlação**: o dataset não permite isolar causas.

## Indicadores de monitoramento (pergunta 10)

Sugeridos para detectar problemas operacionais, todos calculáveis com os marts:

1. **Taxa de atraso** por UF e por mês (`mart_regional_operations`): alerta se subir acima da média histórica (6,8%).
2. **Dias de despacho** (compra → transportadora) por vendedor (`mart_seller_performance`): vendedores com despacho muito acima da mediana.
3. **Taxa de cancelamento e de indisponibilidade** por mês (`mart_sales_daily`).
4. **Nota média e % de notas ≤ 2** por faixa de atraso e por categoria; queda de nota em pedidos *no prazo* indica problema de produto, não de logística.
5. **Pedidos sem entrega após a data estimada** ainda em `shipped`/`processing` (backlog).
6. **Frete médio por faixa de distância**, para detectar frete fora do padrão.
7. **Indicadores de qualidade de dados** (veja `data_quality.md`): volume de anomalias de timestamp e de divergência de pagamento.
