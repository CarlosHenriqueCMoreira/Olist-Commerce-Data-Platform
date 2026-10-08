"""Tabela de controle raw.ingestion_runs: uma linha por arquivo e por execução."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ingestion.config import RAW_SCHEMA

DDL = f"""
CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA};
CREATE TABLE IF NOT EXISTS {RAW_SCHEMA}.ingestion_runs (
    run_id        uuid        NOT NULL,
    source_file   text        NOT NULL,
    file_checksum text        NOT NULL,
    row_count     bigint,
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz,
    status        text        NOT NULL CHECK (status IN ('running','success','failed','skipped')),
    error_message text,
    PRIMARY KEY (run_id, source_file)
);
"""


def ensure_control_table(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(DDL))


def start_run(engine: Engine, run_id: str, source_file: str, checksum: str) -> None:
    """Registra 'running' numa transação própria: sobrevive a falhas da carga."""
    with engine.begin() as conn:
        conn.execute(
            text(
                f"INSERT INTO {RAW_SCHEMA}.ingestion_runs (run_id, source_file, file_checksum, status)"
                " VALUES (:run_id, :source_file, :checksum, 'running')"
            ),
            {"run_id": run_id, "source_file": source_file, "checksum": checksum},
        )


def finish_run(
    engine: Engine,
    run_id: str,
    source_file: str,
    status: str,
    row_count: int | None = None,
    error_message: str | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                f"UPDATE {RAW_SCHEMA}.ingestion_runs SET status = :status, row_count = :row_count,"
                " error_message = :error, finished_at = now()"
                " WHERE run_id = :run_id AND source_file = :source_file"
            ),
            {
                "status": status,
                "row_count": row_count,
                "error": error_message,
                "run_id": run_id,
                "source_file": source_file,
            },
        )


def last_success_checksum(engine: Engine, source_file: str) -> str | None:
    with engine.connect() as conn:
        return conn.execute(
            text(
                f"SELECT file_checksum FROM {RAW_SCHEMA}.ingestion_runs"
                " WHERE source_file = :f AND status = 'success'"
                " ORDER BY finished_at DESC LIMIT 1"
            ),
            {"f": source_file},
        ).scalar_one_or_none()
