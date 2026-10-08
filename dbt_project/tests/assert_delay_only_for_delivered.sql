-- Regra: atraso só existe para pedidos entregues com data de entrega.
select order_id
from {{ ref('fct_orders') }}
where is_delayed and not has_delivery_date
