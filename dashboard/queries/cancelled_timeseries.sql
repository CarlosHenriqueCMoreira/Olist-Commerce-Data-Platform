-- fonte: marts.mart_sales_daily
select
    date_trunc('month', purchase_date)::date as period,
    sum(cancelled_orders) as cancelled,
    sum(unavailable_orders) as unavailable
from marts.mart_sales_daily
where purchase_date between :start_date and :end_date
  and (cardinality(CAST(:states AS text[])) = 0 or customer_state = any(CAST(:states AS text[])))
group by 1 order by 1
