{#- Grão: um item de pedido. Desnormalizado para análise por categoria, vendedor e estado. -#}
select
    i.order_item_key,
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    o.customer_id,
    o.purchase_date,
    o.purchase_month,
    o.customer_state,
    i.seller_state,
    i.category_name,
    o.order_status,
    o.is_revenue_order,
    o.is_delayed,
    o.review_score,
    i.price,
    i.freight_value,
    i.distance_km
from {{ ref('int_order_items_enriched') }} i
join {{ ref('fct_orders') }} o using (order_id)
