select
    {{ clean_text('geolocation_zip_code_prefix') }}  as zip_code_prefix,
    cast(geolocation_lat as double precision)         as latitude,
    cast(geolocation_lng as double precision)         as longitude,
    {{ clean_lower('geolocation_city') }}             as city,
    upper({{ clean_text('geolocation_state') }})      as state,
    source_file,
    ingested_at
from {{ source('raw', 'geolocation') }}
