-- Reconciliação: nenhum pedido some entre raw e fct_orders.
with r as (select count(*) as n from {{ source('raw', 'orders') }}),
     f as (select count(*) as n from {{ ref('fct_orders') }})
select r.n as raw_orders, f.n as fct_orders from r, f where r.n <> f.n
