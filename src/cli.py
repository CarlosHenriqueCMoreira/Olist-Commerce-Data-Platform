"""CLI do projeto: python -m src.cli {check-files,validate,load,export}."""

from __future__ import annotations

import argparse
import logging
import sys

from ingestion.config import SOURCES, ConfigError, get_data_dir
from ingestion.load_raw import DatabaseConnectionError, load_all, make_engine
from ingestion.validate_files import ValidationError, validate_all


def cmd_check_files(_: argparse.Namespace) -> int:
    data_dir = get_data_dir()
    missing = [name for name, _cols in SOURCES.values() if not (data_dir / name).is_file()]
    if missing:
        print(f"Arquivos ausentes em {data_dir}:\n  " + "\n  ".join(missing), file=sys.stderr)
        return 1
    print(f"OK: {len(SOURCES)} arquivos encontrados em {data_dir}")
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    infos = validate_all()
    print(f"{'arquivo':45} {'bytes':>12} {'linhas':>10}  sha256")
    for i in infos:
        print(f"{i.path.name:45} {i.size_bytes:>12,} {i.row_count:>10,}  {i.checksum[:12]}…")
    return 0


def cmd_load(args: argparse.Namespace) -> int:
    results = load_all(force=args.force)
    for r in results:
        print(f"{r.table:40} {r.status:8} {r.rows:>10,}")
    return 0


def cmd_export(_: argparse.Namespace) -> int:
    from src.export import export_marts

    manifest = export_marts(make_engine())
    for table, rows in manifest["tables"].items():
        print(f"{table:40} {rows:>10,} linhas")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="olist", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check-files", help="confere se os 9 CSVs existem").set_defaults(
        func=cmd_check_files
    )
    sub.add_parser("validate", help="valida colunas, vazio, linhas e checksum").set_defaults(
        func=cmd_validate
    )
    load = sub.add_parser("load", help="carrega os CSVs no schema raw (idempotente)")
    load.add_argument("--force", action="store_true", help="recarrega mesmo sem mudança no arquivo")
    load.set_defaults(func=cmd_load)
    sub.add_parser("export", help="exporta marts para data/exports").set_defaults(func=cmd_export)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValidationError, ConfigError, DatabaseConnectionError, RuntimeError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
