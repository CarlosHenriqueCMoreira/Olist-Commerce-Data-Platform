select
    d::date                                         as date_day,
    extract(year from d)::int                       as year,
    extract(quarter from d)::int                    as quarter,
    extract(month from d)::int                      as month,
    to_char(d, 'YYYY-MM')                           as year_month,
    date_trunc('month', d)::date                    as month_start,
    extract(isodow from d)::int                     as iso_day_of_week,
    to_char(d, 'Dy')                                as day_name,
    extract(isodow from d) in (6, 7)                as is_weekend
from generate_series('2016-01-01'::date, '2018-12-31'::date, interval '1 day') as d
