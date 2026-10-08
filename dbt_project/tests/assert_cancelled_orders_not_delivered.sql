-- Regra: pedido cancelado não pode ter sido entregue ao cliente.
-- A origem tem 6 violações conhecidas: aviso até 50, falha acima disso.
{{ config(severity='error', warn_if='>0', error_if='>50') }}
select order_id, order_status, delivered_at
from {{ ref('fct_orders') }}
where is_cancelled and delivered_at is not null
