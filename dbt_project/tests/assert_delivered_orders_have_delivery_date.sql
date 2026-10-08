-- Regra: pedido 'delivered' deve ter data de entrega.
-- A origem tem 8 violações conhecidas (docs/data_quality.md): aviso até 50, falha acima disso.
{{ config(severity='error', warn_if='>0', error_if='>50') }}
select order_id, order_status, delivered_at
from {{ ref('fct_orders') }}
where is_delivered and delivered_at is null
