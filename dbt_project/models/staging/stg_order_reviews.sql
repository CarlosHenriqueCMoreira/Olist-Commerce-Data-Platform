{#- review_id NÃO é único na origem (814 repetições entre pedidos distintos); a chave é (review_id, order_id). -#}
select
    md5(coalesce(review_id, '') || '|' || coalesce(order_id, ''))   as review_key,
    {{ clean_text('review_id') }}                                   as review_id,
    {{ clean_text('order_id') }}                                    as order_id,
    cast(review_score as integer)                                   as review_score,
    {{ clean_text('review_comment_title') }}                        as review_comment_title,
    {{ clean_text('review_comment_message') }}                      as review_comment_message,
    cast(nullif(review_creation_date, '') as timestamp)             as review_created_at,
    cast(nullif(review_answer_timestamp, '') as timestamp)          as review_answered_at,
    source_file,
    ingested_at
from {{ source('raw', 'order_reviews') }}
