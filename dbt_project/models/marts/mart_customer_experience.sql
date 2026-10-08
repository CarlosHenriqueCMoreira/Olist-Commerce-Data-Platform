{#- Grão: mês x faixa de atraso x nota. Mostra o impacto do atraso na avaliação. -#}
select
    purchase_month,
    delay_bucket,
    review_score,
    count(*) as orders
from {{ ref('fct_orders') }}
where review_score is not null
group by purchase_month, delay_bucket, review_score
