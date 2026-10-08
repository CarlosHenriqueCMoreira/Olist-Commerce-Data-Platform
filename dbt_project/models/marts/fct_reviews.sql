select
    review_key,
    review_id,
    order_id,
    review_score,
    review_score <= {{ var('low_review_max') }}                  as is_low_review,
    review_comment_message is not null                           as has_comment,
    review_created_at,
    review_answered_at
from {{ ref('stg_order_reviews') }}
