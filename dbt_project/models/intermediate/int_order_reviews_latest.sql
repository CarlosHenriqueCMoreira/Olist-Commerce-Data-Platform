{#- 547 pedidos têm mais de uma avaliação: usamos a mais recente (answered_at, desempate por review_key). -#}
with ranked as (
    select
        order_id,
        review_score,
        review_created_at,
        count(*) over (partition by order_id) as reviews_count,
        row_number() over (
            partition by order_id
            order by review_answered_at desc nulls last, review_created_at desc nulls last, review_key
        ) as rn
    from {{ ref('stg_order_reviews') }}
)

select order_id, review_score, review_created_at, reviews_count
from ranked
where rn = 1
