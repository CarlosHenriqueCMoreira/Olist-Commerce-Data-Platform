-- fonte: marts.mart_sales_daily
select
    date_trunc(:grain, purchase_date)::date as period,
    sum(orders)                              as orders,
    sum(products_revenue)                    as products_revenue,
    sum(freight_revenue)                     as freight_revenue
from marts.mart_sales_daily
where purchase_date between :start_date and :end_date
  and (cardinality(CAST(:states AS text[])) = 0 or customer_state = any(CAST(:states AS text[])))
  and (cardinality(CAST(:statuses AS text[])) = 0 or order_status = any(CAST(:statuses AS text[])))
group by 1 order by 1
