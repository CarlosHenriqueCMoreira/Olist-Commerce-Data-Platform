"""Acesso a dados do dashboard: executa os .sql de dashboard/queries contra os marts."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

QUERIES_DIR = Path(__file__).parent / "queries"
load_dotenv(Path(__file__).parent.parent / ".env")


def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        database=os.environ["POSTGRES_DB"],
    )
    return create_engine(url, pool_pre_ping=True)


def run_query(engine, name: str, **params) -> pd.DataFrame:
    sql = (QUERIES_DIR / f"{name}.sql").read_text()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)
