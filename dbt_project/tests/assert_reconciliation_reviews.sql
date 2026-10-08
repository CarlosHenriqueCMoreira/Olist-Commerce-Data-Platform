-- Reconciliação: toda avaliação da origem existe em fct_reviews, e cada pedido avaliado tem nota em fct_orders.
with r as (select count(*) as n from {{ source('raw', 'order_reviews') }}),
     f as (select count(*) as n from {{ ref('fct_reviews') }}),
     rated_raw as (select count(distinct order_id) as n from {{ source('raw', 'order_reviews') }}),
     rated_fct as (select count(*) as n from {{ ref('fct_orders') }} where review_score is not null)
select r.n as raw_reviews, f.n as fct_reviews, rated_raw.n as raw_rated_orders, rated_fct.n as fct_rated_orders
from r, f, rated_raw, rated_fct
where r.n <> f.n or rated_raw.n <> rated_fct.n
