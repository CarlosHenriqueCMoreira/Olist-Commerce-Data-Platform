-- fonte: marts.mart_delivery_performance
select
    distance_bucket,
    sum(orders)                                                           as orders,
    sum(freight_sum) / nullif(sum(orders_with_items), 0)                  as avg_freight,
    sum(total_days_sum) / nullif(sum(delivered_with_date_orders), 0)      as avg_delivery_days,
    sum(review_score_sum) / nullif(sum(review_count), 0)                  as avg_score
from marts.mart_delivery_performance
where purchase_month between date_trunc('month', CAST(:start_date AS date)) and :end_date
  and distance_bucket <> 'unknown'
group by 1
order by min(case distance_bucket when '0-99 km' then 1 when '100-499 km' then 2
                 when '500-999 km' then 3 when '1000-1999 km' then 4 else 5 end)
