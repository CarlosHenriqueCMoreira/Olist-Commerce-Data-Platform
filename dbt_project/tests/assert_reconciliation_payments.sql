-- Reconciliação: pagamentos raw = fct_payments = total por pedido em fct_orders.
with r as (select sum(payment_value::numeric) as v, count(*) as n from {{ source('raw', 'order_payments') }}),
     f as (select sum(payment_value) as v, count(*) as n from {{ ref('fct_payments') }}),
     o as (select sum(payments_total) as v from {{ ref('fct_orders') }})
select r.v as raw_value, f.v as fct_value, o.v as orders_value
from r, f, o
where r.v <> f.v or r.v <> o.v or r.n <> f.n
