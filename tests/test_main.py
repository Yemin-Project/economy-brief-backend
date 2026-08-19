import logging
from pathlib import Path

import pytest

from app import main
from app.analyzer import Brief, Issue
from app.collector import Article


def _article() -> Article:
    return Article(
        id="001-001234567",
        section_type="headline",
        display_position=1,
        title="테스트 기사",
        description="테스트 설명문",
        source="테스트 뉴스",
        url="https://example.com/article",
        cluster_url=None,
        related_count=None,
        collected_at="2026-08-19T00:00:00+00:00",
    )


def test_run_batch_records_a_successful_execution(monkeypatch, tmp_path: Path, caplog) -> None:
    recorded: dict[str, object] = {}
    monkeypatch.setattr(main, "load_dotenv", lambda: None)
    monkeypatch.setattr(main, "initialize_database", lambda: None)
    monkeypatch.setattr(main, "create_batch_run", lambda: 7)
    monkeypatch.setattr(main, "collect_headlines", lambda limit: [_article()])
    monkeypatch.setattr(
        main,
        "analyze_articles",
        lambda articles: Brief(
            overall_summary="테스트 전체 요약입니다.",
            issues=[
                Issue(
                    keyword="테스트",
                    importance="low",
                    summary="테스트 이슈 요약입니다.",
                    related_article_ids=["001-001234567"],
                )
            ],
        ),
    )
    monkeypatch.setattr(main, "render_markdown", lambda brief, articles: "# 테스트 리포트\n")
    monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path)

    def record_success(batch_run_id: int, **kwargs: object) -> None:
        recorded["batch_run_id"] = batch_run_id
        recorded.update(kwargs)

    monkeypatch.setattr(main, "mark_batch_run_success", record_success)

    with caplog.at_level(logging.INFO, logger="app.main"):
        result = main.run_batch()

    assert result.batch_run_id == 7
    assert result.article_count == 1
    assert result.articles_path.exists()
    assert result.report_path.exists()
    assert recorded["batch_run_id"] == 7
    assert recorded["article_count"] == 1
    assert recorded["articles_file"] == result.articles_path.name
    assert recorded["report_file"] == result.report_path.name
    assert isinstance(recorded["duration_seconds"], float)
    assert "event=batch_started batch_run_id=7" in caplog.text
    assert "event=batch_completed batch_run_id=7 status=success" in caplog.text


def test_run_batch_records_a_failed_execution(monkeypatch, caplog) -> None:
    recorded: dict[str, object] = {}
    monkeypatch.setattr(main, "load_dotenv", lambda: None)
    monkeypatch.setattr(main, "initialize_database", lambda: None)
    monkeypatch.setattr(main, "create_batch_run", lambda: 8)

    def fail_collection(limit: int) -> list[Article]:
        raise RuntimeError("수집 실패")

    def record_failure(batch_run_id: int, **kwargs: object) -> None:
        recorded["batch_run_id"] = batch_run_id
        recorded.update(kwargs)

    monkeypatch.setattr(main, "collect_headlines", fail_collection)
    monkeypatch.setattr(main, "mark_batch_run_failed", record_failure)

    with caplog.at_level(logging.INFO, logger="app.main"):
        with pytest.raises(RuntimeError, match="수집 실패"):
            main.run_batch()

    assert recorded["batch_run_id"] == 8
    assert recorded["error_message"] == "수집 실패"
    assert isinstance(recorded["duration_seconds"], float)
    assert "event=batch_completed batch_run_id=8 status=failed" in caplog.text
