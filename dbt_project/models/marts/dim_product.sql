select
    p.product_id,
    p.category_name_pt,
    coalesce(t.category_name_en, p.category_name_pt, 'unknown')  as category_name,
    p.name_length,
    p.description_length,
    p.photos_qty,
    p.weight_g,
    p.length_cm,
    p.height_cm,
    p.width_cm,
    p.length_cm * p.height_cm * p.width_cm                       as volume_cm3
from {{ ref('stg_products') }} p
left join {{ ref('stg_product_category_translation') }} t using (category_name_pt)
