"""Gera um dataset SINTÉTICO (determinístico) no formato dos 9 CSVs da Olist.

Uso: python scripts/generate_sample_data.py data/sample [n_orders]

Serve para o CI e para testar o pipeline sem o dataset real (não versionado por licença).
Os dados são fictícios e respeitam as regras de integridade verificadas pelo dbt.
Não use estes números para análise.
"""

from __future__ import annotations

import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ingestion.config import SOURCES  # noqa: E402

CITIES = {
    "SP": ("sao paulo", -23.55, -46.63),
    "RJ": ("rio de janeiro", -22.90, -43.20),
    "MG": ("belo horizonte", -19.92, -43.94),
    "BA": ("salvador", -12.97, -38.50),
    "RS": ("porto alegre", -30.03, -51.23),
    "AM": ("manaus", -3.12, -60.02),
}
CATEGORIES = {
    "beleza_saude": "health_beauty",
    "informatica_acessorios": "computers_accessories",
    "cama_mesa_banho": "bed_bath_table",
    "esporte_lazer": "sports_leisure",
    "pc_gamer": None,  # sem tradução (como na origem)
}
STATUS_WEIGHTS = [
    ("delivered", 90),
    ("shipped", 3),
    ("canceled", 3),
    ("unavailable", 2),
    ("processing", 1),
    ("invoiced", 1),
]


def hexid(rng: random.Random) -> str:
    return f"{rng.getrandbits(128):032x}"


def ts(d: datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%S")


def generate(out: Path, n_orders: int = 400, seed: int = 42) -> None:
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    states = list(CITIES)

    # geolocalização: 3 prefixos por UF; alguns prefixos de clientes ficam sem geolocalização
    geo, zips = [], {}
    for uf, (city, lat, lng) in CITIES.items():
        zips[uf] = []
        for k in range(3):
            z = f"{rng.randint(10, 99)}{rng.randint(100, 999)}"
            zips[uf].append(z)
            for _ in range(2):
                geo.append(
                    [
                        z,
                        lat + rng.uniform(-0.2, 0.2) + k * 0.1,
                        lng + rng.uniform(-0.2, 0.2),
                        city,
                        uf,
                    ]
                )

    sellers = []
    for _ in range(15):
        uf = rng.choice(states)
        sellers.append([hexid(rng), rng.choice(zips[uf]), CITIES[uf][0], uf])

    products = []
    for i in range(40):
        cat = rng.choice(list(CATEGORIES) + [None]) if i else None
        products.append(
            [
                hexid(rng),
                cat or "",
                rng.randint(20, 60),
                rng.randint(100, 900),
                rng.randint(1, 5),
                rng.randint(100, 5000),
                rng.randint(10, 60),
                rng.randint(5, 40),
                rng.randint(5, 40),
            ]
        )

    customers = []
    for _ in range(n_orders):
        uf = rng.choice(states)
        zip_code = rng.choice(zips[uf]) if rng.random() > 0.05 else "00000"
        customers.append([hexid(rng), hexid(rng), zip_code, CITIES[uf][0], uf])

    orders, items, payments, reviews = [], [], [], []
    statuses = [s for s, w in STATUS_WEIGHTS for _ in range(w)]
    for cust in customers:
        oid = hexid(rng)
        status = rng.choice(statuses)
        buy = datetime(2017, 1, 1) + timedelta(seconds=rng.randint(0, 600 * 86400))
        approved = buy + timedelta(hours=rng.randint(0, 24))
        shipped = approved + timedelta(days=rng.randint(1, 4), hours=rng.randint(0, 12))
        delivered = shipped + timedelta(days=rng.randint(2, 20))
        estimated = (buy + timedelta(days=rng.randint(8, 25))).replace(hour=0, minute=0, second=0)
        cols = {"approved": "", "shipped": "", "delivered": ""}
        if status != "unavailable" and status != "canceled" or rng.random() < 0.5:
            cols["approved"] = ts(approved)
        if status in ("delivered", "shipped"):
            cols["shipped"] = ts(shipped)
        if status == "delivered":
            cols["delivered"] = ts(delivered)
        orders.append(
            [
                oid,
                cust[0],
                status,
                ts(buy),
                cols["approved"],
                cols["shipped"],
                cols["delivered"],
                ts(estimated),
            ]
        )

        if status == "unavailable":
            continue
        total = 0.0
        for n in range(1, rng.randint(1, 3) + 1):
            price, freight = round(rng.uniform(10, 400), 2), round(rng.uniform(5, 60), 2)
            total += price + freight
            items.append(
                [
                    oid,
                    n,
                    rng.choice(products)[0],
                    rng.choice(sellers)[0],
                    ts(approved + timedelta(days=3)),
                    price,
                    freight,
                ]
            )
        if status != "canceled" or rng.random() < 0.5:
            installments = rng.randint(1, 6)
            kind = rng.choice(["credit_card", "boleto", "voucher", "debit_card"])
            if rng.random() < 0.2:  # pagamento dividido em duas formas
                part = round(total * 0.4, 2)
                payments += [
                    [oid, 1, "voucher", 1, part],
                    [oid, 2, "credit_card", installments, round(total - part, 2)],
                ]
            else:
                payments.append([oid, 1, kind, installments, round(total, 2)])
        if status == "delivered" and rng.random() < 0.9:
            late = delivered.date() > estimated.date()
            score = rng.choice([1, 1, 2, 3]) if late else rng.choice([3, 4, 5, 5, 5])
            rid = hexid(rng)
            reviews.append(
                [
                    rid,
                    oid,
                    score,
                    "",
                    "ótimo\nproduto" if score > 3 else "",
                    ts(delivered),
                    ts(delivered + timedelta(days=1)),
                ]
            )
            if rng.random() < 0.05:  # segunda avaliação no mesmo pedido
                reviews.append(
                    [
                        hexid(rng),
                        oid,
                        rng.randint(1, 5),
                        "",
                        "",
                        ts(delivered),
                        ts(delivered + timedelta(days=3)),
                    ]
                )
    # review_id repetido entre pedidos distintos (como na origem)
    if len(reviews) > 3:
        reviews.append(
            [reviews[0][0], orders[1][0], 4, "", "", "2017-06-01 00:00:00", "2017-06-02 00:00:00"]
        )

    translation = [[pt, en] for pt, en in CATEGORIES.items() if en]
    data = {
        "orders": orders,
        "order_items": items,
        "order_payments": payments,
        "order_reviews": reviews,
        "products": products,
        "customers": customers,
        "sellers": sellers,
        "geolocation": geo,
        "product_category_name_translation": translation,
    }
    for table, rows in data.items():
        filename, columns = SOURCES[table]
        with (out / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            writer.writerows(rows)
    print(f"Dataset sintético gerado em {out} ({len(orders)} pedidos, {len(items)} itens)")


if __name__ == "__main__":
    generate(
        Path(sys.argv[1] if len(sys.argv) > 1 else "data/sample"),
        int(sys.argv[2]) if len(sys.argv) > 2 else 400,
    )
