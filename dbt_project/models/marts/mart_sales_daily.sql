{#- Grão: dia da compra x UF do cliente x status. Só medidas aditivas: razões são calculadas em quem consome. -#}
select
    purchase_date,
    customer_state,
    order_status,
    count(*)                                                              as orders,
    sum(items_count)                                                      as items,
    sum(products_value)                                                   as gross_products_value,
    sum(products_value) filter (where is_revenue_order)                   as products_revenue,
    sum(freight_value) filter (where is_revenue_order)                    as freight_revenue,
    count(*) filter (where is_revenue_order and items_count > 0)               as revenue_orders,
    count(*) filter (where is_delivered)                                  as delivered_orders,
    count(*) filter (where has_delivery_date)                             as delivered_with_date_orders,
    count(*) filter (where is_delayed)                                    as delayed_orders,
    count(*) filter (where is_cancelled)                                  as cancelled_orders,
    count(*) filter (where is_unavailable)                                as unavailable_orders,
    sum(days_purchase_to_delivery) filter (where has_delivery_date and days_purchase_to_delivery is not null) as delivery_days_sum,
    count(*) filter (where has_delivery_date and days_purchase_to_delivery is not null)                       as total_days_orders,
    sum(review_score)                                                     as review_score_sum,
    count(review_score)                                                   as review_count
from {{ ref('fct_orders') }}
group by purchase_date, customer_state, order_status
