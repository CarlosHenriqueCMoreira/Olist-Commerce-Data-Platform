-- Regra estrutural: as flags são mutuamente exclusivas (cancelado nunca conta como entregue).
select order_id
from {{ ref('fct_orders') }}
where is_cancelled and is_delivered
