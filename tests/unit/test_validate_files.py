import hashlib

import pytest

from ingestion.config import SOURCES
from ingestion.validate_files import (
    ValidationError,
    count_rows,
    sha256_of,
    validate_all,
    validate_file,
)


def test_validate_ok(tiny_data_dir):
    infos = validate_all(tiny_data_dir)
    assert len(infos) == len(SOURCES)
    assert all(i.row_count == 2 and i.size_bytes > 0 for i in infos)


def test_checksum_matches_hashlib_and_changes_with_content(tmp_path):
    f = tmp_path / "a.csv"
    f.write_bytes(b"a,b\n1,2\n")
    assert sha256_of(f) == hashlib.sha256(b"a,b\n1,2\n").hexdigest()
    before = sha256_of(f)
    f.write_bytes(b"a,b\n1,3\n")
    assert sha256_of(f) != before


def test_missing_file_has_clear_message(tmp_path):
    with pytest.raises(ValidationError, match="Arquivo ausente"):
        validate_file("orders", tmp_path)


def test_validate_all_reports_every_missing_file(tmp_path):
    with pytest.raises(ValidationError) as exc:
        validate_all(tmp_path)
    assert str(exc.value).count("Arquivo ausente") == len(SOURCES)


def test_empty_file(tiny_data_dir):
    (tiny_data_dir / SOURCES["orders"][0]).write_text("")
    with pytest.raises(ValidationError, match="vazio"):
        validate_file("orders", tiny_data_dir)


def test_header_only_file(tiny_data_dir):
    path = tiny_data_dir / SOURCES["sellers"][0]
    path.write_text(",".join(SOURCES["sellers"][1]) + "\n")
    with pytest.raises(ValidationError, match="nenhuma linha"):
        validate_file("sellers", tiny_data_dir)


def test_missing_required_column(tiny_data_dir):
    path = tiny_data_dir / SOURCES["sellers"][0]
    path.write_text("seller_id,seller_city\n1,x\n")
    with pytest.raises(ValidationError, match="colunas obrigatórias ausentes"):
        validate_file("sellers", tiny_data_dir)


def test_bom_in_header_is_accepted(tiny_data_dir):
    name, cols = SOURCES["product_category_name_translation"]
    (tiny_data_dir / name).write_text(",".join(cols) + "\na,b\n", encoding="utf-8-sig")
    assert validate_file("product_category_name_translation", tiny_data_dir).row_count == 1


def test_count_rows_handles_multiline_quoted_fields(tmp_path):
    f = tmp_path / "r.csv"
    f.write_text('id,msg\n1,"linha1\nlinha2"\n2,ok\n', encoding="utf-8")
    assert count_rows(f) == 2
