with by_type as (
    select
        order_id,
        payment_type,
        sum(payment_value) as type_value
    from {{ ref('stg_order_payments') }}
    group by order_id, payment_type
),

main_type as (
    -- método principal = o de maior valor pago; empate resolvido em ordem alfabética
    select distinct on (order_id) order_id, payment_type as main_payment_type
    from by_type
    order by order_id, type_value desc, payment_type
),

totals as (
    select
        order_id,
        count(*)                    as payments_count,
        sum(payment_value)          as payments_total,
        max(payment_installments)   as max_installments
    from {{ ref('stg_order_payments') }}
    group by order_id
)

select t.*, m.main_payment_type
from totals t
join main_type m using (order_id)
