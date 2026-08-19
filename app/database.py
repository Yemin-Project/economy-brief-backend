"""PostgreSQL connection and schema setup for batch execution history."""

from __future__ import annotations

import os

import psycopg
from psycopg import Connection


def connect() -> Connection:
    """Create a connection from one set of PostgreSQL environment variables."""
    database_name = _required_env("POSTGRES_DB")
    database_user = _required_env("POSTGRES_USER")
    database_password = _required_env("POSTGRES_PASSWORD")
    database_host = "db"
    database_port = os.getenv("POSTGRES_PORT", "5432")
    return psycopg.connect(
        host=database_host,
        port=database_port,
        dbname=database_name,
        user=database_user,
        password=database_password,
    )


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name}이 없습니다. .env 파일 또는 실행 환경에 설정하세요.")
    return value


def initialize_database() -> None:
    """Create the small schema required by Version 1 if it does not exist."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS batch_runs (
                id BIGSERIAL PRIMARY KEY,
                status VARCHAR(16) NOT NULL CHECK (status IN ('running', 'success', 'failed')),
                started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                finished_at TIMESTAMPTZ,
                duration_seconds DOUBLE PRECISION,
                article_count INTEGER,
                articles_file TEXT,
                report_file TEXT,
                error_message TEXT
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS batch_runs_started_at_idx ON batch_runs (started_at DESC)"
        )
