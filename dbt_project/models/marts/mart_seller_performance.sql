{#- Grão: vendedor x mês da compra. Despacho = compra -> entrega à transportadora. -#}
select
    so.seller_id,
    d.state                                                           as seller_state,
    so.purchase_month,
    count(*)                                                          as orders,
    count(*) filter (where so.is_cancelled)                           as cancelled_orders,
    count(*) filter (where so.is_delivered)                           as delivered_orders,
    count(*) filter (where so.has_delivery_date)                      as delivered_with_date_orders,
    count(*) filter (where so.is_delayed)                             as delayed_orders,
    sum(so.products_value) filter (where so.is_revenue_order)         as products_revenue,
    sum(so.freight_value) filter (where so.is_revenue_order)          as freight_revenue,
    count(*) filter (where so.is_revenue_order)                       as revenue_orders,
    sum(so.days_purchase_to_carrier)                                  as dispatch_days_sum,
    count(so.days_purchase_to_carrier)                                as dispatch_orders,
    sum(so.review_score)                                              as review_score_sum,
    count(so.review_score)                                            as review_count
from {{ ref('int_seller_orders') }} so
join {{ ref('dim_seller') }} d using (seller_id)
group by so.seller_id, d.state, so.purchase_month
