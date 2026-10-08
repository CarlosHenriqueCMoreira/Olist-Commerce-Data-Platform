import pytest
from sqlalchemy import text

from ingestion import load_raw, metadata
from ingestion.config import RAW_SCHEMA, SOURCES
from ingestion.validate_files import validate_all

pytestmark = pytest.mark.integration


def _count(engine, table):
    return load_raw.table_row_count(engine, table)


def test_first_load_then_second_load_does_not_duplicate(pg_engine, tiny_data_dir):
    first = load_raw.load_all(engine=pg_engine, data_dir=tiny_data_dir)
    assert {r.status for r in first} == {"success"}
    assert all(_count(pg_engine, t) == 2 for t in SOURCES)

    second = load_raw.load_all(engine=pg_engine, data_dir=tiny_data_dir)
    assert {r.status for r in second} == {"skipped"}
    assert all(_count(pg_engine, t) == 2 for t in SOURCES)

    forced = load_raw.load_all(force=True, engine=pg_engine, data_dir=tiny_data_dir)
    assert {r.status for r in forced} == {"success"}
    assert all(_count(pg_engine, t) == 2 for t in SOURCES)  # recarga substitui, não acumula


def test_changed_file_is_reloaded(pg_engine, tiny_data_dir):
    load_raw.load_all(engine=pg_engine, data_dir=tiny_data_dir)
    name, cols = SOURCES["sellers"]
    with (tiny_data_dir / name).open("a") as f:
        f.write(",".join(f"x{i}" for i, _ in enumerate(cols)) + "\n")
    results = {r.table: r for r in load_raw.load_all(engine=pg_engine, data_dir=tiny_data_dir)}
    assert results["sellers"].status == "success" and _count(pg_engine, "sellers") == 3
    assert results["orders"].status == "skipped"


def test_trace_columns_and_run_history(pg_engine, tiny_data_dir):
    load_raw.load_all(engine=pg_engine, data_dir=tiny_data_dir)
    with pg_engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT source_file, ingested_at FROM {RAW_SCHEMA}.sellers LIMIT 1")
        ).one()
        runs = conn.execute(
            text(
                f"SELECT count(*), count(*) FILTER (WHERE status='success') FROM {RAW_SCHEMA}.ingestion_runs"
            )
        ).one()
    assert row.source_file == SOURCES["sellers"][0] and row.ingested_at is not None
    assert runs == (len(SOURCES), len(SOURCES))


def test_failed_load_rolls_back_and_is_recorded(pg_engine, tiny_data_dir):
    load_raw.load_all(engine=pg_engine, data_dir=tiny_data_dir)
    info = next(i for i in validate_all(tiny_data_dir) if i.table == "sellers")
    # força inconsistência: o arquivo diz ter mais linhas do que realmente tem
    bad = type(info)(info.table, info.path, info.size_bytes, info.row_count + 5, "other-checksum")
    metadata.ensure_control_table(pg_engine)
    result = load_raw.load_file(pg_engine, bad, "00000000-0000-0000-0000-000000000001")
    assert result.status == "failed"
    assert _count(pg_engine, "sellers") == 2  # tabela intacta
    with pg_engine.connect() as conn:
        status, err = conn.execute(
            text(
                f"SELECT status, error_message FROM {RAW_SCHEMA}.ingestion_runs"
                " WHERE run_id = '00000000-0000-0000-0000-000000000001'"
            )
        ).one()
    assert status == "failed" and "esperadas" in err
