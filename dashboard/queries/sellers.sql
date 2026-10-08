-- fonte: marts.mart_seller_performance
select
    seller_id,
    max(seller_state)                                                       as seller_state,
    sum(orders)                                                             as orders,
    coalesce(sum(products_revenue), 0)                                      as products_revenue,
    sum(products_revenue) / nullif(sum(revenue_orders), 0)                  as avg_order_value,
    sum(dispatch_days_sum) / nullif(sum(dispatch_orders), 0)                as avg_dispatch_days,
    sum(delayed_orders)::float / nullif(sum(delivered_with_date_orders), 0) as delay_rate,
    sum(review_score_sum) / nullif(sum(review_count), 0)                    as avg_score,
    sum(cancelled_orders)::float / nullif(sum(orders), 0)                   as cancel_rate
from marts.mart_seller_performance
where purchase_month between date_trunc('month', CAST(:start_date AS date)) and :end_date
  and (cardinality(CAST(:sellers AS text[])) = 0 or seller_id = any(CAST(:sellers AS text[])))
group by 1
having sum(orders) >= :min_orders
order by products_revenue desc
