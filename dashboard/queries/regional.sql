-- fonte: marts.mart_regional_operations
select
    customer_state,
    sum(orders)                                                           as orders,
    sum(delayed_orders)::float / nullif(sum(delivered_with_date_orders), 0) as delay_rate,
    sum(delivery_days_sum) / nullif(sum(total_days_orders), 0)                as avg_delivery_days,
    sum(freight_sum) / nullif(sum(orders_with_items), 0)                  as avg_freight,
    sum(review_score_sum) / nullif(sum(review_count), 0)                  as avg_score
from marts.mart_regional_operations
where purchase_month between date_trunc('month', CAST(:start_date AS date)) and :end_date
  and (cardinality(CAST(:states AS text[])) = 0 or customer_state = any(CAST(:states AS text[])))
group by 1
order by orders desc
