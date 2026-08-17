from pathlib import Path

from fastapi.testclient import TestClient

from app import api
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
            article_count=10,
            articles_path=Path("outputs/articles_20260817_070000.json"),
            report_path=Path("outputs/morning_brief_20260817_070000.md"),
        ),
    )

    response = TestClient(api.app).post("/batch/run")

    assert response.status_code == 201
    assert response.json() == {
        "status": "completed",
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
