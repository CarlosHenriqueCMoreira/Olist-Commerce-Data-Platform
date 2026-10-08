-- Regra: dentro de cada pedido, order_item_id começa em 1, não repete e não tem lacunas (1..N).
select
    order_id,
    min(order_item_id) as first_item,
    max(order_item_id) as last_item,
    count(*)           as items
from {{ ref('fct_order_items') }}
group by order_id
having min(order_item_id) <> 1
    or max(order_item_id) <> count(*)
    or count(distinct order_item_id) <> count(*)
