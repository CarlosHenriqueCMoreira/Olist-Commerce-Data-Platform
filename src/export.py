"""Exporta os marts para data/exports (CSV) e grava um manifesto com contagens de linhas."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from ingestion.config import PROJECT_ROOT

EXPORT_DIR = PROJECT_ROOT / "data" / "exports"


def export_marts(engine: Engine, out_dir: Path = EXPORT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    with engine.connect() as conn:
        tables = [
            r[0]
            for r in conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables"
                    " WHERE table_schema = 'marts' AND table_name LIKE 'mart\\_%' ORDER BY 1"
                )
            )
        ]
        if not tables:
            raise RuntimeError("Nenhum mart_* encontrado no schema marts. Rode o dbt antes.")
        manifest = {"exported_at": datetime.now(UTC).isoformat(), "tables": {}}
        for table in tables:
            df = pd.read_sql(text(f'SELECT * FROM marts."{table}"'), conn)
            df.to_csv(out_dir / f"{table}.csv", index=False)
            manifest["tables"][table] = len(df)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
