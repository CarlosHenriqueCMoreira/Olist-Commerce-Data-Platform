"""Acesso a dados do dashboard: executa os .sql de dashboard/queries contra os marts."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ingestion.config import get_db_config  # noqa: E402

QUERIES_DIR = Path(__file__).parent / "queries"


def get_engine():
    return create_engine(get_db_config().url(), pool_pre_ping=True)


def run_query(engine, name: str, **params) -> pd.DataFrame:
    sql = (QUERIES_DIR / f"{name}.sql").read_text()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)
