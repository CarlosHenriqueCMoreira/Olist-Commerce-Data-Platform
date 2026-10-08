{#- Item x atributos do pedido: base das métricas de produto/categoria. A nota é do pedido, replicada em cada item. -#}
select
    i.order_item_key,
    i.order_id,
    i.product_id,
    i.category_name,
    i.weight_g,
    i.volume_cm3,
    i.price,
    i.freight_value,
    o.purchased_at::date                      as purchase_date,
    date_trunc('month', o.purchased_at)::date as purchase_month,
    o.order_status,
    o.is_revenue_order,
    o.review_score,
    (o.review_score is not null)              as has_review,
    coalesce(o.review_score <= {{ var('low_review_max') }}, false) as is_low_review
from {{ ref('int_order_items_enriched') }} i
join {{ ref('int_orders_enriched') }} o using (order_id)
