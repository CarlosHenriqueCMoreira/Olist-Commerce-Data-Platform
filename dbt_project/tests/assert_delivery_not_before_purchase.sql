-- Regra: a entrega ao cliente não pode ser anterior à compra. Qualquer violação falha o build.
select order_id, purchased_at, delivered_at
from {{ ref('fct_orders') }}
where delivered_at < purchased_at
