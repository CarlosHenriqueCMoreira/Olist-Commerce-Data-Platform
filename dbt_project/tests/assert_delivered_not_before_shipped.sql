-- Anomalia da origem: entrega ao cliente antes da entrega à transportadora (~23 pedidos).
-- Duração de trânsito descartada nas métricas; falha se passar de 500 pedidos.
{{ config(severity='error', warn_if='>0', error_if='>500') }}
select order_id, shipped_at, delivered_at
from {{ ref('fct_orders') }}
where delivered_at < shipped_at
