{#- Grão: produto x mês da compra. Agregue por category_name para a visão de categoria. -#}
select
    product_id,
    category_name,
    purchase_month,
    count(*) filter (where is_revenue_order)                         as units_sold,
    sum(price) filter (where is_revenue_order)                       as revenue,
    sum(freight_value) filter (where is_revenue_order)               as freight_sum,
    count(*)                                                         as items,
    count(*) filter (where has_review)                               as reviewed_items,
    sum(review_score)                                                as review_score_sum,
    count(*) filter (where is_low_review)                            as low_review_items,
    max(weight_g)                                                    as weight_g,
    max(volume_cm3)                                                  as volume_cm3
from {{ ref('int_product_items') }}
group by product_id, category_name, purchase_month
