-- fonte: marts.mart_delivery_performance
select
    sum(approval_days_sum) / nullif(sum(approval_orders), 0) as approval_days,
    sum(dispatch_days_sum) / nullif(sum(dispatch_orders), 0) as dispatch_days,
    sum(transit_days_sum)  / nullif(sum(transit_orders), 0)  as transit_days,
    sum(total_days_sum) / nullif(sum(delivered_with_date_orders), 0) as total_days
from marts.mart_delivery_performance
where purchase_month between date_trunc('month', CAST(:start_date AS date)) and :end_date
