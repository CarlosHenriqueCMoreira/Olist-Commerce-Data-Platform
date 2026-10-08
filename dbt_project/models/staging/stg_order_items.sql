select
    {{ clean_text('order_id') }}                           as order_id,
    cast(order_item_id as integer)                         as order_item_id,
    {{ clean_text('product_id') }}                         as product_id,
    {{ clean_text('seller_id') }}                          as seller_id,
    cast(nullif(shipping_limit_date, '') as timestamp)     as shipping_limit_at,
    cast(price as numeric(12, 2))                          as price,
    cast(freight_value as numeric(12, 2))                  as freight_value,
    source_file,
    ingested_at
from {{ source('raw', 'order_items') }}
