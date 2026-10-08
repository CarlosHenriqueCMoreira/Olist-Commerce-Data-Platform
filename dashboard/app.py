"""Dashboard Streamlit. Toda métrica vem dos marts (schema marts) via dashboard/queries/*.sql."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from data import get_engine, run_query  # noqa: E402

ACCENT = "#2a6fdb"
WARN = "#d9534f"
GRID = "#e6e6e6"
DELAY_ORDER = ["on_time", "late_1_3d", "late_4_7d", "late_8d_plus", "not_delivered"]
DELAY_LABELS = {
    "on_time": "No prazo",
    "late_1_3d": "Atraso 1-3 d",
    "late_4_7d": "Atraso 4-7 d",
    "late_8d_plus": "Atraso 8+ d",
    "not_delivered": "Não entregue",
}

st.set_page_config(page_title="Olist Commerce Data Platform", layout="wide")


@st.cache_resource
def engine():
    return get_engine()


@st.cache_data(ttl=600, show_spinner=False)
def q(name: str, **params):
    return run_query(engine(), name, **params)


def style(fig, height=340):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=30, b=8),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor=GRID, title_text="")
    fig.update_yaxes(gridcolor=GRID)
    return fig


def brl(v) -> str:
    return "—" if v is None else f"R$ {v:,.0f}".replace(",", ".")


def pct(v) -> str:
    return "—" if v is None or v != v else f"{v * 100:.1f}%"


def num(v, digits=1, suffix="") -> str:
    return "—" if v is None or v != v else f"{v:.{digits}f}{suffix}"


# --------------------------------------------------------------------------- dados / filtros
try:
    meta = q("meta").iloc[0]
except Exception as exc:  # banco fora do ar ou marts não construídos
    st.error(
        "Não consegui ler os marts. Suba o banco e rode o pipeline: `make pipeline`.\n\n"
        f"Detalhe: {exc.__class__.__name__}"
    )
    st.stop()

first_date: date = meta["first_date"]
last_date: date = meta["last_date"]

with st.sidebar:
    st.header("Filtros")
    period = st.date_input(
        "Período da compra", (first_date, last_date), min_value=first_date, max_value=last_date
    )
    if not isinstance(period, tuple) or len(period) != 2:
        st.info("Selecione data inicial e final.")
        st.stop()
    start_date, end_date = period
    states = st.multiselect("Estado do cliente (UF)", list(meta["states"]))
    statuses = st.multiselect("Status do pedido", list(meta["statuses"]))
    categories = st.multiselect(
        "Categoria do produto", q("categories_list")["category_name"].tolist()
    )
    sellers = st.multiselect("Vendedor", q("sellers_list")["seller_id"].tolist())
    grain = st.radio(
        "Granularidade da série",
        ["month", "day"],
        format_func=lambda g: {"month": "Mensal", "day": "Diária"}[g],
        horizontal=True,
    )
    st.caption(
        "Período, UF e status filtram as visões de vendas e operação. Categoria filtra a aba "
        "Produtos; vendedor filtra a aba Vendedores."
    )

common = dict(start_date=start_date, end_date=end_date, states=states)
with_status = dict(common, statuses=statuses)

st.title("Olist Commerce Data Platform")
st.caption(
    f"Dados históricos e anonimizados da Olist, compras de {first_date:%d/%m/%Y} a {last_date:%d/%m/%Y}. "
    "Fonte: Kaggle (CC BY-NC-SA 4.0). Relações mostradas são correlações, não causalidade."
)

tab_exec, tab_ops, tab_cx, tab_sellers, tab_products, tab_about = st.tabs(
    [
        "Visão executiva",
        "Operação",
        "Experiência e frete",
        "Vendedores",
        "Produtos",
        "Sobre os dados",
    ]
)

# --------------------------------------------------------------------------- executiva
with tab_exec:
    k = q("kpis", **with_status).iloc[0]
    c = st.columns(4)
    c[0].metric("Pedidos", f"{int(k['orders']):,}".replace(",", "."))
    c[1].metric("Receita de produtos", brl(k["products_revenue"]))
    c[2].metric("Receita de frete", brl(k["freight_revenue"]))
    c[3].metric("Ticket médio", brl(k["avg_ticket"]))
    c = st.columns(4)
    c[0].metric("Taxa de entrega", pct(k["delivery_rate"]))
    c[1].metric(
        "Taxa de atraso",
        pct(k["delay_rate"]),
        help="Entregues com data de entrega após a estimada, sobre entregues com data.",
    )
    c[2].metric("Nota média", num(k["avg_score"], 2))
    c[3].metric("Prazo médio de entrega", num(k["avg_delivery_days"], 1, " dias"))
    st.caption(
        "Receita exclui pedidos cancelados e indisponíveis. Frete é reportado separado da receita de produtos."
    )

    ts = q("sales_timeseries", grain=grain, **with_status)
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Evolução de pedidos e receita")
        metric = st.radio(
            "Métrica",
            ["products_revenue", "orders"],
            format_func=lambda m: "Receita de produtos" if m == "products_revenue" else "Pedidos",
            horizontal=True,
        )
        fig = px.line(ts, x="period", y=metric, color_discrete_sequence=[ACCENT])
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig), width="stretch")
    with right:
        st.subheader("Pedidos por status")
        sb = q("status_breakdown", **common)
        fig = px.bar(
            sb, x="orders", y="order_status", orientation="h", color_discrete_sequence=[ACCENT]
        )
        fig.update_yaxes(title_text="", autorange="reversed")
        fig.update_xaxes(title_text="", type="log")
        st.plotly_chart(style(fig), width="stretch")
        st.caption("Eixo logarítmico: 'delivered' domina a base.")

# --------------------------------------------------------------------------- operação
with tab_ops:
    st.subheader("Tempo por etapa do pedido (dias, média)")
    ds = q("delivery_stages", **{k_: v for k_, v in common.items() if k_ != "states"}).iloc[0]
    c = st.columns(4)
    c[0].metric("Compra → aprovação", num(ds["approval_days"], 2))
    c[1].metric("Compra → envio", num(ds["dispatch_days"], 2))
    c[2].metric("Envio → entrega", num(ds["transit_days"], 2))
    c[3].metric("Compra → entrega", num(ds["total_days"], 2))
    st.caption(
        "Etapas com ordem temporal impossível na origem são excluídas da média (veja docs/data_quality.md). Esta seção não usa o filtro de UF."
    )

    left, right = st.columns(2)
    reg = q("regional", **common)
    with left:
        st.subheader("Regiões com maior atraso")
        top = reg[reg["orders"] >= 100].sort_values("delay_rate", ascending=False).head(10)
        fig = px.bar(
            top, x="delay_rate", y="customer_state", orientation="h", color_discrete_sequence=[WARN]
        )
        fig.update_yaxes(title_text="", autorange="reversed")
        fig.update_xaxes(title_text="", tickformat=".0%")
        st.plotly_chart(style(fig), width="stretch")
        st.caption("UFs com pelo menos 100 pedidos no período.")
    with right:
        st.subheader("Pedidos e prazo de entrega por UF")
        fig = px.scatter(
            reg,
            x="orders",
            y="avg_delivery_days",
            text="customer_state",
            color_discrete_sequence=[ACCENT],
        )
        fig.update_traces(textposition="top center")
        fig.update_xaxes(title_text="Pedidos", type="log")
        fig.update_yaxes(title_text="Dias até a entrega")
        st.plotly_chart(style(fig), width="stretch")

    st.subheader("Pedidos cancelados e indisponíveis por mês")
    canc = q("cancelled_timeseries", **common).melt("period", var_name="tipo", value_name="pedidos")
    canc["tipo"] = canc["tipo"].map({"cancelled": "Cancelados", "unavailable": "Indisponíveis"})
    fig = px.bar(
        canc,
        x="period",
        y="pedidos",
        color="tipo",
        barmode="stack",
        color_discrete_sequence=[WARN, "#999999"],
    )
    st.plotly_chart(style(fig, 300), width="stretch")

# --------------------------------------------------------------------------- experiência e frete
with tab_cx:
    period_only = {k_: v for k_, v in common.items() if k_ != "states"}
    left, right = st.columns(2)
    with left:
        st.subheader("Nota média por situação de entrega")
        dv = q("delay_vs_score", **period_only)
        dv["situacao"] = dv["delay_bucket"].map(DELAY_LABELS)
        fig = px.bar(
            dv,
            x="situacao",
            y="avg_score",
            color_discrete_sequence=[ACCENT],
            text=dv["avg_score"].round(2),
        )
        fig.update_yaxes(range=[0, 5], title_text="Nota média")
        st.plotly_chart(style(fig), width="stretch")
        st.caption(
            "Pedidos atrasados têm notas bem menores, mas atraso e nota ocorrem juntos por vários motivos; isto é correlação, não prova de causa."
        )
    with right:
        st.subheader("Frete, prazo e nota por distância")
        dist = q("distance", **period_only)
        fig = px.bar(
            dist,
            x="distance_bucket",
            y="avg_freight",
            color_discrete_sequence=[ACCENT],
            text=dist["avg_freight"].round(1),
        )
        fig.update_yaxes(title_text="Frete médio por pedido (R$)")
        st.plotly_chart(style(fig), width="stretch")
    st.dataframe(
        dist.rename(
            columns={
                "distance_bucket": "Distância cliente-vendedor",
                "orders": "Pedidos",
                "avg_freight": "Frete médio (R$)",
                "avg_delivery_days": "Dias até entrega",
                "avg_score": "Nota média",
            }
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Distância haversine entre centróides de CEP (aproximada). Pedidos sem geolocalização ficam de fora."
    )

# --------------------------------------------------------------------------- vendedores
with tab_sellers:
    min_orders = st.slider("Mínimo de pedidos por vendedor", 1, 200, 30)
    sl = q(
        "sellers", start_date=start_date, end_date=end_date, sellers=sellers, min_orders=min_orders
    )
    st.caption(
        f"{len(sl)} vendedores com pelo menos {min_orders} pedidos no período. Nota do pedido é atribuída a todos os vendedores do pedido."
    )
    view = sl.rename(
        columns={
            "seller_id": "Vendedor",
            "seller_state": "UF",
            "orders": "Pedidos",
            "products_revenue": "Receita (R$)",
            "avg_order_value": "Valor médio (R$)",
            "avg_dispatch_days": "Despacho (dias)",
            "delay_rate": "Taxa de atraso",
            "avg_score": "Nota média",
            "cancel_rate": "% cancelados",
        }
    )
    left, right = st.columns(2)
    with left:
        st.subheader("Melhores (nota média)")
        st.dataframe(
            view.sort_values(["Nota média", "Pedidos"], ascending=False).head(10),
            hide_index=True,
            width="stretch",
        )
    with right:
        st.subheader("Piores (nota média)")
        st.dataframe(
            view.sort_values(["Nota média", "Pedidos"], ascending=[True, False]).head(10),
            hide_index=True,
            width="stretch",
        )
    st.subheader("Maiores receitas")
    st.dataframe(view.head(20), hide_index=True, width="stretch")

# --------------------------------------------------------------------------- produtos
with tab_products:
    cats = q("categories", start_date=start_date, end_date=end_date, categories=categories)
    left, right = st.columns(2)
    with left:
        st.subheader("Receita por categoria (top 15)")
        top = cats.sort_values("revenue", ascending=False).head(15)
        fig = px.bar(
            top, x="revenue", y="category_name", orientation="h", color_discrete_sequence=[ACCENT]
        )
        fig.update_yaxes(title_text="", autorange="reversed")
        fig.update_xaxes(title_text="R$")
        st.plotly_chart(style(fig, 460), width="stretch")
    with right:
        st.subheader("Maior taxa de avaliações baixas")
        min_rev = st.slider("Mínimo de itens avaliados", 50, 1000, 200, step=50)
        low = (
            cats[cats["reviewed_items"] >= min_rev]
            .sort_values("low_review_rate", ascending=False)
            .head(15)
        )
        fig = px.bar(
            low,
            x="low_review_rate",
            y="category_name",
            orientation="h",
            color_discrete_sequence=[WARN],
        )
        fig.update_yaxes(title_text="", autorange="reversed")
        fig.update_xaxes(title_text="", tickformat=".0%")
        st.plotly_chart(style(fig, 460), width="stretch")
        st.caption(
            "Avaliação baixa = nota 1 ou 2. A nota pertence ao pedido e é replicada nos itens dele."
        )
    st.dataframe(cats.sort_values("revenue", ascending=False), hide_index=True, width="stretch")

# --------------------------------------------------------------------------- sobre
with tab_about:
    st.markdown(f"""
**Escopo e limites**
- Dataset histórico e anonimizado, sem atualização esperada. Compras de **{first_date:%d/%m/%Y}** a **{last_date:%d/%m/%Y}**.
- Não há dados de abandono de carrinho, recomendações ou atendimento; o painel não mede esses fenômenos.
- Atraso = entregue com data de entrega posterior (em dias) à estimada. Pedido não entregue não é atraso.
- Receita de produtos exclui cancelados e indisponíveis e é separada do frete.
- Correlações (ex.: atraso x nota) não implicam causalidade.

**Rastreabilidade:** cada gráfico indica o mart de origem na query em `dashboard/queries/`.
Definições completas em `docs/metrics.md`. Licença dos dados: CC BY-NC-SA 4.0 (uso não comercial, com atribuição).
""")
