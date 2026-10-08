{#- Seller x pedido: base das métricas de vendedor (um pedido pode ter vários vendedores). -#}
select
    i.seller_id,
    i.order_id,
    o.purchased_at::date                      as purchase_date,
    date_trunc('month', o.purchased_at)::date as purchase_month,
    o.order_status,
    o.is_delivered,
    o.is_cancelled,
    o.is_revenue_order,
    o.has_delivery_date,
    o.is_delayed,
    o.days_purchase_to_carrier,
    o.review_score,
    count(*)                                  as items_count,
    sum(i.price)                              as products_value,
    sum(i.freight_value)                      as freight_value
from {{ ref('int_order_items_enriched') }} i
join {{ ref('int_orders_enriched') }} o using (order_id)
group by
    i.seller_id, i.order_id, o.purchased_at, o.order_status, o.is_delivered, o.is_cancelled,
    o.is_revenue_order, o.has_delivery_date, o.is_delayed, o.days_purchase_to_carrier, o.review_score
