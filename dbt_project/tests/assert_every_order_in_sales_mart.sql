-- Nenhum pedido desaparece: soma de pedidos do mart = pedidos em fct_orders.
select m.n as mart_orders, f.n as fct_orders
from (select sum(orders) as n from {{ ref('mart_sales_daily') }}) m,
     (select count(*) as n from {{ ref('fct_orders') }}) f
where m.n <> f.n
