select
    s.seller_id,
    s.zip_code_prefix,
    s.city,
    s.state,
    l.latitude,
    l.longitude
from {{ ref('stg_sellers') }} s
left join {{ ref('int_zip_locations') }} l using (zip_code_prefix)
