"""Persistence helpers for the lifecycle of one batch execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.database import connect


@dataclass(frozen=True)
class BatchRun:
    id: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: float | None
    article_count: int | None
    articles_file: str | None
    report_file: str | None
    error_message: str | None


def _to_batch_run(row: tuple[object, ...]) -> BatchRun:
    return BatchRun(
        id=int(row[0]),
        status=str(row[1]),
        started_at=row[2],  # type: ignore[arg-type]
        finished_at=row[3],  # type: ignore[arg-type]
        duration_seconds=float(row[4]) if row[4] is not None else None,
        article_count=int(row[5]) if row[5] is not None else None,
        articles_file=str(row[6]) if row[6] is not None else None,
        report_file=str(row[7]) if row[7] is not None else None,
        error_message=str(row[8]) if row[8] is not None else None,
    )


_BATCH_RUN_COLUMNS = """
    id, status, started_at, finished_at, duration_seconds,
    article_count, articles_file, report_file, error_message
"""


def list_batch_runs(limit: int = 20) -> list[BatchRun]:
    """Return the most recent batch runs first."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            f"SELECT {_BATCH_RUN_COLUMNS} FROM batch_runs ORDER BY started_at DESC LIMIT %s",
            (limit,),
        )
        return [_to_batch_run(row) for row in cursor.fetchall()]


def get_batch_run(batch_run_id: int) -> BatchRun | None:
    """Return one batch run, or None when the ID does not exist."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            f"SELECT {_BATCH_RUN_COLUMNS} FROM batch_runs WHERE id = %s",
            (batch_run_id,),
        )
        row = cursor.fetchone()
    return _to_batch_run(row) if row else None


def create_batch_run() -> int:
    """Record the start of a batch before calling external services."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("INSERT INTO batch_runs (status) VALUES ('running') RETURNING id")
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("배치 실행 이력을 생성하지 못했습니다.")
    return int(row[0])


def mark_batch_run_success(
    batch_run_id: int,
    *,
    duration_seconds: float,
    article_count: int,
    articles_file: str,
    report_file: str,
) -> None:
    """Complete a batch execution after its output files are safely written."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE batch_runs
            SET status = 'success',
                finished_at = NOW(),
                duration_seconds = %s,
                article_count = %s,
                articles_file = %s,
                report_file = %s,
                error_message = NULL
            WHERE id = %s
            """,
            (duration_seconds, article_count, articles_file, report_file, batch_run_id),
        )
        if cursor.rowcount != 1:
            raise RuntimeError(f"배치 실행 이력 {batch_run_id}를 찾지 못했습니다.")


def mark_batch_run_failed(
    batch_run_id: int,
    *,
    duration_seconds: float,
    error_message: str,
) -> None:
    """Persist the failure reason without replacing the original batch exception."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE batch_runs
            SET status = 'failed',
                finished_at = NOW(),
                duration_seconds = %s,
                error_message = %s
            WHERE id = %s
            """,
            (duration_seconds, error_message, batch_run_id),
        )
        if cursor.rowcount != 1:
            raise RuntimeError(f"배치 실행 이력 {batch_run_id}를 찾지 못했습니다.")
