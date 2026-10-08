from src import cli


def test_check_files_ok_and_missing(tiny_data_dir, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "get_data_dir", lambda: tiny_data_dir)
    assert cli.main(["check-files"]) == 0
    monkeypatch.setattr(cli, "get_data_dir", lambda: tmp_path / "vazio")
    assert cli.main(["check-files"]) == 1
    assert "Arquivos ausentes" in capsys.readouterr().err


def test_validate_failure_returns_nonzero(tmp_path, monkeypatch, capsys):
    import ingestion.validate_files as vf

    monkeypatch.setattr(vf, "get_data_dir", lambda: tmp_path)
    assert cli.main(["validate"]) == 1
    assert "ERRO" in capsys.readouterr().err
