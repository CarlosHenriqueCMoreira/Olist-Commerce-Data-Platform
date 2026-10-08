select
    {{ clean_text('customer_id') }}               as customer_id,
    {{ clean_text('customer_unique_id') }}        as customer_unique_id,
    {{ clean_text('customer_zip_code_prefix') }}  as zip_code_prefix,
    {{ clean_lower('customer_city') }}            as city,
    upper({{ clean_text('customer_state') }})     as state,
    source_file,
    ingested_at
from {{ source('raw', 'customers') }}
