select
    {{ clean_lower('product_category_name') }}          as category_name_pt,
    {{ clean_lower('product_category_name_english') }}  as category_name_en,
    source_file,
    ingested_at
from {{ source('raw', 'product_category_name_translation') }}
