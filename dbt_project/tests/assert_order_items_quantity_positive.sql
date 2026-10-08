-- Regra: a quantidade de itens de um pedido com itens é positiva e o sequencial começa em 1.
select order_id
from {{ ref('fct_orders') }}
where items_count < 0
union all
select order_id
from {{ ref('fct_order_items') }}
where order_item_id < 1
