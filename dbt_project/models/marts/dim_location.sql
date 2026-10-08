select
    zip_code_prefix,
    city,
    state,
    latitude,
    longitude,
    geolocation_points
from {{ ref('int_zip_locations') }}
