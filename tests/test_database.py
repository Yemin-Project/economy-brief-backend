import pytest

from app import database


def test_connect_uses_postgres_environment_variables(monkeypatch) -> None:
    captured: dict[str, str] = {}
    monkeypatch.setenv("POSTGRES_DB", "example_db")
    monkeypatch.setenv("POSTGRES_USER", "example_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "example_password")
    monkeypatch.setattr(database.psycopg, "connect", lambda **kwargs: captured.update(kwargs))

    database.connect()

    assert captured == {
        "host": "db",
        "port": "5432",
        "dbname": "example_db",
        "user": "example_user",
        "password": "example_password",
    }


def test_connect_requires_postgres_credentials(monkeypatch) -> None:
    monkeypatch.delenv("POSTGRES_DB", raising=False)

    with pytest.raises(RuntimeError, match="POSTGRES_DB"):
        database.connect()
