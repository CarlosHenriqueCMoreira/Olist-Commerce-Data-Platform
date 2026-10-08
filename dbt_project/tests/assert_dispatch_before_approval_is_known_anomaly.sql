-- Anomalia da origem: envio à transportadora antes da aprovação do pagamento (~1.4% dos pedidos).
-- Não distorce as métricas (despacho é medido desde a COMPRA), mas é monitorada: falha se passar de 3%.
{{ config(severity='error', warn_if='>0', error_if='>3000') }}
select order_id, approved_at, shipped_at
from {{ ref('fct_orders') }}
where shipped_at < approved_at
