-- fonte: marts.mart_product_performance
select
    category_name,
    coalesce(sum(units_sold), 0)                                     as units_sold,
    coalesce(sum(revenue), 0)                                        as revenue,
    sum(revenue) / nullif(sum(units_sold), 0)                        as avg_price,
    sum(freight_sum) / nullif(sum(units_sold), 0)                    as avg_freight,
    sum(review_score_sum) / nullif(sum(reviewed_items), 0)           as avg_score,
    sum(low_review_items)::float / nullif(sum(reviewed_items), 0)    as low_review_rate,
    sum(reviewed_items)                                              as reviewed_items
from marts.mart_product_performance
where purchase_month between date_trunc('month', CAST(:start_date AS date)) and :end_date
  and (cardinality(CAST(:categories AS text[])) = 0 or category_name = any(CAST(:categories AS text[])))
group by 1
