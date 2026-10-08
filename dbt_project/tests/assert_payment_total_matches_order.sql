-- Regra: soma dos pagamentos ~ produtos + frete, dentro da tolerância (var payment_tolerance, R$ 1,00).
-- A origem tem divergências legítimas (juros de parcelamento, vouchers): aviso até 500 pedidos
-- (~0,5% da base), falha acima disso. Veja docs/data_quality.md.
{{ config(severity='error', warn_if='>0', error_if='>500') }}
select order_id, total_value, payments_total
from {{ ref('fct_orders') }}
where payments_total is not null
  and items_count > 0
  and abs(payments_total - total_value) > {{ var('payment_tolerance') }}
