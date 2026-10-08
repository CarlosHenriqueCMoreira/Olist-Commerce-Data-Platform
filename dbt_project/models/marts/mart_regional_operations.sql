{#- Grão: mês da compra x UF do cliente. -#}
select
    purchase_month,
    customer_state,
    count(*)                                                         as orders,
    count(*) filter (where is_cancelled)                             as cancelled_orders,
    count(*) filter (where has_delivery_date)                        as delivered_with_date_orders,
    count(*) filter (where is_delayed)                               as delayed_orders,
    sum(days_purchase_to_delivery) filter (where has_delivery_date and days_purchase_to_delivery is not null) as delivery_days_sum,
    count(*) filter (where has_delivery_date and days_purchase_to_delivery is not null)                       as total_days_orders,
    sum(freight_value) filter (where items_count > 0)                as freight_sum,
    count(*) filter (where items_count > 0)                          as orders_with_items,
    sum(products_value) filter (where is_revenue_order)              as products_revenue,
    sum(review_score)                                                as review_score_sum,
    count(review_score)                                              as review_count
from {{ ref('fct_orders') }}
group by purchase_month, customer_state
