select
    {{ clean_text('order_id') }}                  as order_id,
    cast(payment_sequential as integer)           as payment_sequential,
    {{ clean_lower('payment_type') }}             as payment_type,
    cast(payment_installments as integer)         as payment_installments,
    cast(payment_value as numeric(12, 2))         as payment_value,
    source_file,
    ingested_at
from {{ source('raw', 'order_payments') }}
