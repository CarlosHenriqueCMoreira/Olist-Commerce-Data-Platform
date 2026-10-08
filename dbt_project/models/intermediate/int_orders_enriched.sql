{#-
  Um pedido por linha. Regras (detalhes em docs/metrics.md e docs/decisions.md):
  - receita de produtos (products_value) é separada do frete (freight_value);
  - is_delivered = status 'delivered'; is_cancelled = status 'canceled';
  - atraso só existe para pedido entregue COM data de entrega: entrega (data) > estimativa (data);
  - is_revenue_order exclui 'canceled' e 'unavailable';
  - durações de etapas com ordem temporal impossível (ex.: envio antes da compra) ficam NULL e fora das médias.
-#}
with orders as (
    select o.*, c.customer_unique_id, c.city as customer_city, c.state as customer_state,
           c.zip_code_prefix as customer_zip
    from {{ ref('stg_orders') }} o
    join {{ ref('stg_customers') }} c using (customer_id)
),

items as (
    select
        order_id,
        count(*)                       as items_count,
        count(distinct seller_id)      as sellers_count,
        sum(price)                     as products_value,
        sum(freight_value)             as freight_value,
        round(avg(distance_km), 1)     as avg_distance_km
    from {{ ref('int_order_items_enriched') }}
    group by order_id
),

joined as (
    select
        o.order_id,
        o.customer_id,
        o.customer_unique_id,
        o.customer_city,
        o.customer_state,
        o.customer_zip,
        o.order_status,
        o.purchased_at,
        o.approved_at,
        o.shipped_at,
        o.delivered_at,
        o.estimated_delivery_at,
        coalesce(i.items_count, 0)          as items_count,
        coalesce(i.sellers_count, 0)        as sellers_count,
        coalesce(i.products_value, 0)       as products_value,
        coalesce(i.freight_value, 0)        as freight_value,
        coalesce(i.products_value, 0) + coalesce(i.freight_value, 0) as total_value,
        i.avg_distance_km,
        p.payments_total,
        p.payments_count,
        p.max_installments,
        p.main_payment_type,
        r.review_score,
        coalesce(r.reviews_count, 0)        as reviews_count
    from orders o
    left join items i using (order_id)
    left join {{ ref('int_order_payments_agg') }} p using (order_id)
    left join {{ ref('int_order_reviews_latest') }} r using (order_id)
),

flags as (
    select
        *,
        order_status = 'delivered'                                   as is_delivered,
        order_status = 'canceled'                                    as is_cancelled,
        order_status = 'unavailable'                                 as is_unavailable,
        order_status not in ('canceled', 'unavailable')              as is_revenue_order,
        (order_status = 'delivered' and delivered_at is not null)    as has_delivery_date,
        {{ days_between_valid('purchased_at', 'approved_at') }}             as days_purchase_to_approval,
        {{ days_between_valid('approved_at', 'shipped_at') }}               as days_approval_to_carrier,
        {{ days_between_valid('purchased_at', 'shipped_at') }}              as days_purchase_to_carrier,
        {{ days_between_valid('shipped_at', 'delivered_at') }}              as days_carrier_to_customer,
        {{ days_between_valid('purchased_at', 'delivered_at') }}            as days_purchase_to_delivery,
        {{ days_between('purchased_at', 'estimated_delivery_at') }}   as days_purchase_to_estimate,
        case when order_status = 'delivered' and delivered_at is not null
             then delivered_at::date - estimated_delivery_at::date end as days_late
    from joined
)

select
    *,
    coalesce(days_late > 0, false)                                   as is_delayed,
    case
        when not has_delivery_date then 'not_delivered'
        when days_late <= 0 then 'on_time'
        when days_late <= 3 then 'late_1_3d'
        when days_late <= 7 then 'late_4_7d'
        else 'late_8d_plus'
    end                                                              as delay_bucket,
    case
        when avg_distance_km is null then 'unknown'
        when avg_distance_km < 100 then '0-99 km'
        when avg_distance_km < 500 then '100-499 km'
        when avg_distance_km < 1000 then '500-999 km'
        when avg_distance_km < 2000 then '1000-1999 km'
        else '2000+ km'
    end                                                              as distance_bucket
from flags
