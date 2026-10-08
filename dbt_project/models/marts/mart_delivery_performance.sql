{#- Grão: mês da compra x faixa de distância cliente-vendedor. Etapas do ciclo + frete + satisfação. -#}
select
    purchase_month,
    distance_bucket,
    count(*)                                                           as orders,
    count(*) filter (where has_delivery_date)                          as delivered_with_date_orders,
    count(*) filter (where is_delayed)                                 as delayed_orders,
    sum(days_purchase_to_approval) filter (where days_purchase_to_approval is not null)          as approval_days_sum,
    count(*) filter (where days_purchase_to_approval is not null)                                as approval_orders,
    sum(days_purchase_to_carrier) filter (where days_purchase_to_carrier is not null)            as dispatch_days_sum,
    count(*) filter (where days_purchase_to_carrier is not null)                                 as dispatch_orders,
    sum(days_carrier_to_customer) filter (where days_carrier_to_customer is not null) as transit_days_sum,
    count(*) filter (where days_carrier_to_customer is not null)           as transit_orders,
    sum(days_purchase_to_delivery) filter (where has_delivery_date and days_purchase_to_delivery is not null) as total_days_sum,
    count(*) filter (where has_delivery_date and days_purchase_to_delivery is not null)                       as total_days_orders,
    sum(freight_value) filter (where items_count > 0)                  as freight_sum,
    count(*) filter (where items_count > 0)                            as orders_with_items,
    sum(review_score)                                                  as review_score_sum,
    count(review_score)                                                as review_count
from {{ ref('fct_orders') }}
group by purchase_month, distance_bucket
