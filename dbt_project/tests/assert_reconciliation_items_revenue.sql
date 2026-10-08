-- Reconciliação: soma de preço e frete é idêntica em raw, fct_order_items, fct_orders e mart_sales_daily
-- (garante que os joins não multiplicam nem perdem receita).
with r as (
    select sum(price::numeric) as price, sum(freight_value::numeric) as freight, count(*) as n
    from {{ source('raw', 'order_items') }}
),
i as (select sum(price) as price, sum(freight_value) as freight, count(*) as n from {{ ref('fct_order_items') }}),
o as (select sum(products_value) as price, sum(freight_value) as freight from {{ ref('fct_orders') }}),
m as (select sum(gross_products_value) as price, sum(items) as n from {{ ref('mart_sales_daily') }})
select r.price as raw_price, i.price as items_price, o.price as orders_price, m.price as mart_price
from r, i, o, m
where r.price <> i.price or r.price <> o.price or r.price <> m.price
   or r.freight <> i.freight or r.freight <> o.freight
   or r.n <> i.n or r.n <> m.n
