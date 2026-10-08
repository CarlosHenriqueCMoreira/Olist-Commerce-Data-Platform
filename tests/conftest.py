import os

# Antes de qualquer import do projeto: testes de integração usam um schema próprio.
os.environ["OLIST_RAW_SCHEMA"] = "raw_test"

import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from ingestion.config import RAW_SCHEMA, SOURCES, ConfigError, get_db_config  # noqa: E402
from ingestion.load_raw import make_engine  # noqa: E402


@pytest.fixture
def tiny_data_dir(tmp_path):
    """Os 9 CSVs com cabeçalho correto e 2 linhas cada (uma com campo multilinha/vazio)."""
    for _table, (filename, columns) in SOURCES.items():
        lines = [",".join(columns)]
        lines.append(",".join(f'"v{i}a"' for i, _ in enumerate(columns)))
        lines.append(
            ",".join("" if i == len(columns) - 1 else f"v{i}b" for i, _ in enumerate(columns))
        )
        (tmp_path / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def pg_engine():
    try:
        get_db_config()
        engine = make_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # sem banco acessível: pula integração
        pytest.skip(f"PostgreSQL indisponível: {exc.__class__.__name__}")
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {RAW_SCHEMA} CASCADE"))
    yield engine
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {RAW_SCHEMA} CASCADE"))
    engine.dispose()


__all__ = ["ConfigError"]
