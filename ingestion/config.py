"""Configuração centralizada: caminhos dos CSVs, contrato de colunas e conexão com o banco."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# configurável só para testes de integração (conftest usa raw_test e nunca toca no schema real)
RAW_SCHEMA = os.environ.get("OLIST_RAW_SCHEMA", "raw")

# tabela raw -> (arquivo CSV, colunas obrigatórias na ordem do arquivo)
SOURCES: dict[str, tuple[str, tuple[str, ...]]] = {
    "orders": (
        "olist_orders_dataset.csv",
        (
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ),
    ),
    "order_items": (
        "olist_order_items_dataset.csv",
        (
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ),
    ),
    "order_payments": (
        "olist_order_payments_dataset.csv",
        (
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ),
    ),
    "order_reviews": (
        "olist_order_reviews_dataset.csv",
        (
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ),
    ),
    "products": (
        "olist_products_dataset.csv",
        (
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ),
    ),
    "customers": (
        "olist_customers_dataset.csv",
        (
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ),
    ),
    "sellers": (
        "olist_sellers_dataset.csv",
        ("seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"),
    ),
    "geolocation": (
        "olist_geolocation_dataset.csv",
        (
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ),
    ),
    "product_category_name_translation": (
        "product_category_name_translation.csv",
        ("product_category_name", "product_category_name_english"),
    ),
}


class ConfigError(RuntimeError):
    """Variável de ambiente obrigatória ausente ou inválida."""


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

    def url(self) -> URL:
        return URL.create(
            "postgresql+psycopg2",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(
            f"Variável de ambiente obrigatória ausente: {name}. "
            "Copie .env.example para .env e preencha os valores."
        )
    return value


def get_db_config() -> DbConfig:
    load_dotenv(PROJECT_ROOT / ".env")
    port_raw = _required("POSTGRES_PORT")
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ConfigError(f"POSTGRES_PORT deve ser inteiro, recebido: {port_raw!r}") from exc
    return DbConfig(
        host=_required("POSTGRES_HOST"),
        port=port,
        database=_required("POSTGRES_DB"),
        user=_required("POSTGRES_USER"),
        password=_required("POSTGRES_PASSWORD"),
    )


def get_data_dir() -> Path:
    load_dotenv(PROJECT_ROOT / ".env")
    raw = os.environ.get("OLIST_DATA_DIR", "data/raw")
    path = Path(raw)
    return path if path.is_absolute() else PROJECT_ROOT / path
