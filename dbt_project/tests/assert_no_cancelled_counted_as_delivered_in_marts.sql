-- Os marts não contam cancelados/indisponíveis como entregues, nem como receita.
select purchase_date, customer_state, order_status
from {{ ref('mart_sales_daily') }}
where (order_status in ('canceled', 'unavailable')
       and (delivered_orders > 0 or coalesce(products_revenue, 0) > 0))
   or (order_status <> 'delivered' and delivered_orders > 0)
