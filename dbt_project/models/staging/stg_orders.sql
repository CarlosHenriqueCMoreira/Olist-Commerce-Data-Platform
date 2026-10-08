select
    {{ clean_text('order_id') }}                                    as order_id,
    {{ clean_text('customer_id') }}                                 as customer_id,
    {{ clean_lower('order_status') }}                               as order_status,
    cast(nullif(order_purchase_timestamp, '') as timestamp)         as purchased_at,
    cast(nullif(order_approved_at, '') as timestamp)                as approved_at,
    cast(nullif(order_delivered_carrier_date, '') as timestamp)     as shipped_at,
    cast(nullif(order_delivered_customer_date, '') as timestamp)    as delivered_at,
    cast(nullif(order_estimated_delivery_date, '') as timestamp)    as estimated_delivery_at,
    source_file,
    ingested_at
from {{ source('raw', 'orders') }}
