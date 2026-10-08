-- Regra: a aprovação não pode ser anterior à compra.
select order_id, purchased_at, approved_at
from {{ ref('fct_orders') }}
where approved_at < purchased_at
