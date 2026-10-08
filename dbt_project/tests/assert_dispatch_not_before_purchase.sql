-- Anomalia da origem: envio à transportadora ANTES da compra (~0,15% dos pedidos).
-- A duração dessas etapas é descartada nas métricas (days_* = NULL); aqui monitoramos o volume:
-- aviso se houver, falha se passar de 500 pedidos (~0,5%).
{{ config(severity='error', warn_if='>0', error_if='>500') }}
select order_id, purchased_at, shipped_at
from {{ ref('fct_orders') }}
where shipped_at < purchased_at
