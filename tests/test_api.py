from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app import api
from app.batch_runs import BatchRun
from app.main import BatchResult


def test_health_returns_ok() -> None:
    response = TestClient(api.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_batch_run_returns_created_file_names(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "run_batch",
        lambda: BatchResult(
            batch_run_id=1,
            article_count=10,
            articles_path=Path("outputs/articles_20260817_070000.json"),
            report_path=Path("outputs/morning_brief_20260817_070000.md"),
        ),
    )

    response = TestClient(api.app).post("/batch/run")

    assert response.status_code == 201
    assert response.json() == {
        "status": "completed",
        "batch_run_id": 1,
        "article_count": 10,
        "articles_file": "articles_20260817_070000.json",
        "report_file": "morning_brief_20260817_070000.md",
    }


def test_latest_report_returns_markdown(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "read_latest_report",
        lambda: api.StoredReport(
            filename="morning_brief_20260817_070000.md",
            created_at="2026-08-16T22:00:00+00:00",
            content="# 경제 Morning Brief",
        ),
    )

    response = TestClient(api.app).get("/reports/latest")

    assert response.status_code == 200
    assert response.json() == {
        "filename": "morning_brief_20260817_070000.md",
        "created_at": "2026-08-16T22:00:00+00:00",
        "content": "# 경제 Morning Brief",
    }


def test_latest_report_returns_not_found_when_no_file_exists(monkeypatch) -> None:
    def raise_not_found() -> None:
        raise FileNotFoundError

    monkeypatch.setattr(api, "read_latest_report", raise_not_found)

    response = TestClient(api.app).get("/reports/latest")

    assert response.status_code == 404
    assert response.json()["detail"] == "아직 생성된 리포트가 없습니다."


def _batch_run(batch_run_id: int = 1) -> BatchRun:
    return BatchRun(
        id=batch_run_id,
        status="success",
        started_at=datetime(2026, 8, 19, 9, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 8, 19, 9, 1, tzinfo=timezone.utc),
        duration_seconds=61.5,
        article_count=10,
        articles_file="articles_20260819_090000.json",
        report_file="morning_brief_20260819_090000.md",
        error_message=None,
    )


def test_batch_run_list_returns_recent_runs(monkeypatch) -> None:
    requested_limits: list[int] = []

    def list_runs(limit: int) -> list[BatchRun]:
        requested_limits.append(limit)
        return [_batch_run()]

    monkeypatch.setattr(api, "list_batch_runs", list_runs)

    response = TestClient(api.app).get("/batch-runs?limit=5")

    assert response.status_code == 200
    assert requested_limits == [5]
    assert response.json()["items"][0]["id"] == 1
    assert response.json()["items"][0]["status"] == "success"
    assert response.json()["items"][0]["started_at"] == "2026-08-19T09:00:00Z"


def test_batch_run_detail_returns_one_run(monkeypatch) -> None:
    monkeypatch.setattr(api, "get_batch_run", lambda batch_run_id: _batch_run(batch_run_id))

    response = TestClient(api.app).get("/batch-runs/9")

    assert response.status_code == 200
    assert response.json()["id"] == 9
    assert response.json()["report_file"] == "morning_brief_20260819_090000.md"


def test_batch_run_detail_returns_not_found_for_unknown_id(monkeypatch) -> None:
    monkeypatch.setattr(api, "get_batch_run", lambda batch_run_id: None)

    response = TestClient(api.app).get("/batch-runs/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "배치 실행 이력을 찾을 수 없습니다."
