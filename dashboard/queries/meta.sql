select
    min(purchase_date) as first_date,
    max(purchase_date) as last_date,
    array_agg(distinct customer_state order by customer_state) as states,
    array_agg(distinct order_status order by order_status) as statuses
from marts.mart_sales_daily
