{#- Um ponto por prefixo de CEP: média das coordenadas válidas (bbox do Brasil) e cidade/UF mais frequentes. -#}
select
    zip_code_prefix,
    avg(latitude)                                   as latitude,
    avg(longitude)                                  as longitude,
    mode() within group (order by city)             as city,
    mode() within group (order by state)            as state,
    count(*)                                        as geolocation_points
from {{ ref('stg_geolocation') }}
where latitude between -35 and 6
  and longitude between -75 and -33
group by zip_code_prefix
