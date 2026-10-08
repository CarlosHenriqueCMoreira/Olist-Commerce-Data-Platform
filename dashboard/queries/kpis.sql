-- fonte: marts.mart_sales_daily
select
    coalesce(sum(orders), 0)                                                as orders,
    coalesce(sum(products_revenue), 0)                                      as products_revenue,
    coalesce(sum(freight_revenue), 0)                                       as freight_revenue,
    coalesce(sum(products_revenue) / nullif(sum(revenue_orders), 0), 0)     as avg_ticket,
    sum(delivered_orders)::float / nullif(sum(orders), 0)                   as delivery_rate,
    sum(delayed_orders)::float / nullif(sum(delivered_with_date_orders), 0) as delay_rate,
    sum(cancelled_orders)::float / nullif(sum(orders), 0)                   as cancel_rate,
    sum(review_score_sum) / nullif(sum(review_count), 0)                    as avg_score,
    sum(delivery_days_sum) / nullif(sum(delivered_with_date_orders), 0)     as avg_delivery_days
from marts.mart_sales_daily
where purchase_date between :start_date and :end_date
  and (cardinality(CAST(:states AS text[])) = 0 or customer_state = any(CAST(:states AS text[])))
  and (cardinality(CAST(:statuses AS text[])) = 0 or order_status = any(CAST(:statuses AS text[])))
