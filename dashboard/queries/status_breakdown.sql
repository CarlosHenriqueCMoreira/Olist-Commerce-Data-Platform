-- fonte: marts.mart_sales_daily
select order_status, sum(orders) as orders
from marts.mart_sales_daily
where purchase_date between :start_date and :end_date
  and (cardinality(CAST(:states AS text[])) = 0 or customer_state = any(CAST(:states AS text[])))
group by 1 order by 2 desc
