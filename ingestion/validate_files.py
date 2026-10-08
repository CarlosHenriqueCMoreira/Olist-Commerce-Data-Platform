"""Validação dos CSVs antes da carga: existência, colunas, vazio, tamanho, linhas e checksum."""

from __future__ import annotations

import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

from ingestion.config import SOURCES, get_data_dir

csv.field_size_limit(sys.maxsize)


class ValidationError(RuntimeError):
    """Arquivo de origem inválido."""


@dataclass(frozen=True)
class FileInfo:
    table: str
    path: Path
    size_bytes: int
    row_count: int
    checksum: str


def sha256_of(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_header(path: Path) -> list[str]:
    # utf-8-sig remove o BOM presente em product_category_name_translation.csv
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return next(csv.reader(handle), [])


def count_rows(path: Path) -> int:
    """Conta registros (não linhas físicas): comentários de reviews têm quebras de linha."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def validate_file(table: str, data_dir: Path | None = None) -> FileInfo:
    filename, required = SOURCES[table]
    path = (data_dir or get_data_dir()) / filename
    if not path.is_file():
        raise ValidationError(
            f"Arquivo ausente: {path}. Veja data/README.md para baixar o dataset."
        )
    size = path.stat().st_size
    if size == 0:
        raise ValidationError(f"Arquivo vazio: {path}")
    header = read_header(path)
    missing = [col for col in required if col not in header]
    if missing:
        raise ValidationError(f"{filename}: colunas obrigatórias ausentes: {missing}")
    if header != list(required):
        raise ValidationError(
            f"{filename}: ordem/conjunto de colunas inesperado.\n"
            f"  esperado: {list(required)}\n  recebido: {header}"
        )
    rows = count_rows(path)
    if rows == 0:
        raise ValidationError(f"{filename}: possui cabeçalho mas nenhuma linha de dados")
    return FileInfo(table, path, size, rows, sha256_of(path))


def validate_all(data_dir: Path | None = None) -> list[FileInfo]:
    """Valida todos os arquivos e reúne todos os erros antes de falhar."""
    infos: list[FileInfo] = []
    errors: list[str] = []
    for table in SOURCES:
        try:
            infos.append(validate_file(table, data_dir))
        except ValidationError as exc:
            errors.append(str(exc))
    if errors:
        raise ValidationError("\n".join(errors))
    return infos
