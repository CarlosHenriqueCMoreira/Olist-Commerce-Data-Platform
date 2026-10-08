{% test non_negative(model, column_name) %}
select * from {{ model }} where {{ column_name }} < 0
{% endtest %}

{% test positive(model, column_name) %}
select * from {{ model }} where {{ column_name }} <= 0
{% endtest %}

{#- Unicidade de combinação de colunas, sem depender do pacote dbt_utils (funciona offline). -#}
{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as n
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
