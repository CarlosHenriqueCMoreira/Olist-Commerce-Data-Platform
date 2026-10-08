"""Carga idempotente dos CSVs para o schema raw.

Estratégia: por arquivo, uma única transação faz COPY para uma tabela temporária,
TRUNCATE da tabela raw e INSERT ... SELECT. Se qualquer passo falhar, nada é alterado
e a execução fica registrada como 'failed'. Se o checksum do arquivo for o mesmo da
última carga bem-sucedida, o arquivo é ignorado ('skipped'), então rodar duas vezes
nunca duplica linhas.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from ingestion import metadata
from ingestion.config import RAW_SCHEMA, SOURCES, DbConfig, get_db_config
from ingestion.validate_files import FileInfo, validate_all

log = logging.getLogger(__name__)


class DatabaseConnectionError(RuntimeError):
    """Não foi possível conectar ao PostgreSQL."""


@dataclass(frozen=True)
class LoadResult:
    table: str
    status: str  # success | skipped | failed
    rows: int | None = None
    error: str | None = None


def make_engine(config: DbConfig | None = None) -> Engine:
    config = config or get_db_config()
    return create_engine(config.url(), pool_pre_ping=True)


def check_connection(engine: Engine) -> None:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise DatabaseConnectionError(
            "Não foi possível conectar ao PostgreSQL. Ele está de pé (make up) e o .env "
            f"está correto?\nDetalhe: {exc.orig}"
        ) from exc


def _create_table_sql(table: str) -> str:
    cols = ", ".join(f'"{c}" text' for c in SOURCES[table][1])
    return (
        f"CREATE TABLE IF NOT EXISTS {RAW_SCHEMA}.{table} ({cols}, "
        "source_file text, ingested_at timestamptz)"
    )


def table_row_count(engine: Engine, table: str) -> int:
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT count(*) FROM {RAW_SCHEMA}.{table}")).scalar_one()


def _copy_into_table(engine: Engine, info: FileInfo) -> int:
    columns = SOURCES[info.table][1]
    col_list = ", ".join(f'"{c}"' for c in columns)
    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            cur.execute(_create_table_sql(info.table))
            cur.execute(
                f"CREATE TEMP TABLE _load ON COMMIT DROP AS "
                f"SELECT {col_list} FROM {RAW_SCHEMA}.{info.table} WITH NO DATA"
            )
            with info.path.open("r", encoding="utf-8-sig", newline="") as handle:
                cur.copy_expert(
                    f"COPY _load ({col_list}) FROM STDIN WITH (FORMAT csv, HEADER true)", handle
                )
            cur.execute(f"TRUNCATE {RAW_SCHEMA}.{info.table}")
            cur.execute(
                f"INSERT INTO {RAW_SCHEMA}.{info.table} ({col_list}, source_file, ingested_at) "
                f"SELECT {col_list}, %s, now() FROM _load",
                (info.path.name,),
            )
            loaded = cur.rowcount
            if loaded != info.row_count:
                raise RuntimeError(
                    f"{info.path.name}: carregadas {loaded} linhas, esperadas {info.row_count}"
                )
        raw_conn.commit()
        return loaded
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()


def load_file(engine: Engine, info: FileInfo, run_id: str, force: bool = False) -> LoadResult:
    name = info.path.name
    metadata.start_run(engine, run_id, name, info.checksum)
    try:
        unchanged = metadata.last_success_checksum(engine, name) == info.checksum
        if unchanged and not force:
            with engine.connect() as conn:
                exists = conn.execute(
                    text("SELECT to_regclass(:t) IS NOT NULL"), {"t": f"{RAW_SCHEMA}.{info.table}"}
                ).scalar_one()
            if exists and table_row_count(engine, info.table) == info.row_count:
                metadata.finish_run(engine, run_id, name, "skipped", info.row_count)
                log.info("%s: sem alterações (checksum igual), carga ignorada", name)
                return LoadResult(info.table, "skipped", info.row_count)
        rows = _copy_into_table(engine, info)
        metadata.finish_run(engine, run_id, name, "success", rows)
        log.info("%s: %d linhas carregadas em %s.%s", name, rows, RAW_SCHEMA, info.table)
        return LoadResult(info.table, "success", rows)
    except Exception as exc:  # registra e propaga como resultado; o chamador decide falhar
        metadata.finish_run(engine, run_id, name, "failed", error_message=str(exc)[:2000])
        log.error("%s: falha na carga: %s", name, exc)
        return LoadResult(info.table, "failed", error=str(exc))


def load_all(force: bool = False, engine: Engine | None = None, data_dir=None) -> list[LoadResult]:
    infos = validate_all(data_dir)
    engine = engine or make_engine()
    check_connection(engine)
    metadata.ensure_control_table(engine)
    run_id = str(uuid.uuid4())
    results = [load_file(engine, info, run_id, force) for info in infos]
    failed = [r for r in results if r.status == "failed"]
    if failed:
        raise RuntimeError(
            "Carga incompleta; arquivos com falha: "
            + ", ".join(f"{r.table} ({r.error})" for r in failed)
        )
    return results
