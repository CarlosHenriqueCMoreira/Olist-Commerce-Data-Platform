-- fonte: marts.mart_customer_experience
select
    delay_bucket,
    sum(orders)                                              as orders,
    sum(review_score * orders)::float / sum(orders)          as avg_score,
    sum(orders) filter (where review_score <= 2)::float / sum(orders) as low_score_rate
from marts.mart_customer_experience
where purchase_month between date_trunc('month', CAST(:start_date AS date)) and :end_date
group by 1
order by min(case delay_bucket when 'on_time' then 1 when 'late_1_3d' then 2
                 when 'late_4_7d' then 3 when 'late_8d_plus' then 4 else 5 end)
