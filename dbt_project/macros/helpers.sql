{#- Texto raw -> NULL se vazio, sem espaços nas pontas -#}
{% macro clean_text(col) -%} nullif(trim({{ col }}), '') {%- endmacro %}

{#- Texto normalizado em minúsculas (cidades, status, categorias) -#}
{% macro clean_lower(col) -%} nullif(lower(trim({{ col }})), '') {%- endmacro %}

{#- Dias (numeric, 2 casas) entre dois timestamps; NULL se algum for NULL -#}
{% macro days_between(start_ts, end_ts) -%}
    round((extract(epoch from ({{ end_ts }} - {{ start_ts }})) / 86400.0)::numeric, 2)
{%- endmacro %}

{#- Como days_between, mas NULL quando a ordem temporal é impossível (fim < início): anomalia da origem.
    O dado bruto continua em staging/fct; só a MÉTRICA de duração ignora o registro. -#}
{% macro days_between_valid(start_ts, end_ts) -%}
    case when {{ end_ts }} >= {{ start_ts }} then {{ days_between(start_ts, end_ts) }} end
{%- endmacro %}

{#- Distância haversine em km entre dois pontos (graus) -#}
{% macro haversine_km(lat1, lng1, lat2, lng2) -%}
    round((2 * 6371 * asin(sqrt(
        power(sin(radians(({{ lat2 }} - {{ lat1 }}) / 2)), 2)
        + cos(radians({{ lat1 }})) * cos(radians({{ lat2 }}))
          * power(sin(radians(({{ lng2 }} - {{ lng1 }}) / 2)), 2)
    )))::numeric, 1)
{%- endmacro %}
