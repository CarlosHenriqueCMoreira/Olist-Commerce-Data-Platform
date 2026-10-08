import pytest

import ingestion.config as config
from ingestion.load_raw import DatabaseConnectionError, check_connection, make_engine


def _clear(monkeypatch):
    # evita que o .env real preencha as variáveis
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None)
    for name in [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]:
        monkeypatch.delenv(name, raising=False)


def test_missing_variable_fails_with_clear_message(monkeypatch):
    _clear(monkeypatch)
    with pytest.raises(config.ConfigError, match="POSTGRES_PORT"):
        config.get_db_config()


def test_invalid_port(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("POSTGRES_PORT", "abc")
    with pytest.raises(config.ConfigError, match="inteiro"):
        config.get_db_config()


def test_config_from_env(monkeypatch):
    _clear(monkeypatch)
    for k, v in {
        "POSTGRES_HOST": "h",
        "POSTGRES_PORT": "1234",
        "POSTGRES_DB": "d",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
    }.items():
        monkeypatch.setenv(k, v)
    cfg = config.get_db_config()
    assert (cfg.host, cfg.port, cfg.database, cfg.user) == ("h", 1234, "d", "u")


def test_connection_error_is_translated():
    cfg = config.DbConfig("127.0.0.1", 1, "x", "x", "x")  # porta fechada
    with pytest.raises(DatabaseConnectionError, match="conectar ao PostgreSQL"):
        check_connection(make_engine(cfg))
