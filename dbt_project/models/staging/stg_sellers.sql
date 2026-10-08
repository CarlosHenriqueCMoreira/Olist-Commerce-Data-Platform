select
    {{ clean_text('seller_id') }}                 as seller_id,
    {{ clean_text('seller_zip_code_prefix') }}    as zip_code_prefix,
    {{ clean_lower('seller_city') }}              as city,
    upper({{ clean_text('seller_state') }})       as state,
    source_file,
    ingested_at
from {{ source('raw', 'sellers') }}
