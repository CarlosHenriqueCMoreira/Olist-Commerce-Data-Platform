{#- Um item por linha, já com produto, categoria, vendedor, localização e distância cliente-vendedor. -#}
with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select o.order_id, c.zip_code_prefix as customer_zip
    from {{ ref('stg_orders') }} o
    join {{ ref('stg_customers') }} c using (customer_id)
),

products as (
    select
        p.product_id,
        coalesce(t.category_name_en, p.category_name_pt, 'unknown') as category_name,
        p.weight_g,
        p.length_cm * p.height_cm * p.width_cm                      as volume_cm3
    from {{ ref('stg_products') }} p
    left join {{ ref('stg_product_category_translation') }} t using (category_name_pt)
)

select
    i.order_id,
    i.order_item_id,
    i.order_id || '-' || i.order_item_id                  as order_item_key,
    i.product_id,
    i.seller_id,
    i.shipping_limit_at,
    i.price,
    i.freight_value,
    p.category_name,
    p.weight_g,
    p.volume_cm3,
    s.state                                               as seller_state,
    s.zip_code_prefix                                     as seller_zip,
    o.customer_zip,
    {{ haversine_km('cz.latitude', 'cz.longitude', 'sz.latitude', 'sz.longitude') }} as distance_km
from items i
join orders o using (order_id)
left join products p using (product_id)
left join {{ ref('stg_sellers') }} s using (seller_id)
left join {{ ref('int_zip_locations') }} cz on cz.zip_code_prefix = o.customer_zip
left join {{ ref('int_zip_locations') }} sz on sz.zip_code_prefix = s.zip_code_prefix
