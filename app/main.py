"""Run the MVP: collect NAVER Economy headlines, analyze them, save a report."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from app.analyzer import analyze_articles
from app.batch_runs import create_batch_run, mark_batch_run_failed, mark_batch_run_success
from app.collector import collect_headlines
from app.database import initialize_database
from app.logging_config import configure_logging
from app.report import render_markdown

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BatchResult:
    batch_run_id: int
    article_count: int
    articles_path: Path
    report_path: Path


@dataclass(frozen=True)
class StoredReport:
    filename: str
    created_at: str
    content: str


def read_latest_report() -> StoredReport:
    """Load the most recently written Markdown report from local storage."""
    report_paths = list(OUTPUT_DIR.glob("morning_brief_*.md"))
    if not report_paths:
        raise FileNotFoundError("아직 생성된 리포트가 없습니다.")

    report_path = max(report_paths, key=lambda path: path.stat().st_mtime)
    created_at = datetime.fromtimestamp(
        report_path.stat().st_mtime, tz=ZoneInfo("Asia/Seoul")
    ).isoformat()
    return StoredReport(
        filename=report_path.name,
        created_at=created_at,
        content=report_path.read_text(encoding="utf-8"),
    )


def run_batch() -> BatchResult:
    """Collect, analyze, and persist one Morning Brief run."""
    load_dotenv()
    configure_logging()
    try:
        initialize_database()
        batch_run_id = create_batch_run()
    except Exception:
        logger.exception("event=batch_initialization_failed")
        raise

    started = perf_counter()
    logger.info("event=batch_started batch_run_id=%s", batch_run_id)

    try:
        logger.info("event=headline_collection_started batch_run_id=%s", batch_run_id)
        articles = collect_headlines(limit=10)
        logger.info(
            "event=headline_collection_completed batch_run_id=%s article_count=%s",
            batch_run_id,
            len(articles),
        )

        logger.info("event=brief_analysis_started batch_run_id=%s", batch_run_id)
        brief = analyze_articles(articles)
        report = render_markdown(brief, articles)

        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        articles_path = OUTPUT_DIR / f"articles_{timestamp}.json"
        articles_path.write_text(
            json.dumps([article.to_dict() for article in articles], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        report_path = OUTPUT_DIR / f"morning_brief_{timestamp}.md"
        report_path.write_text(report, encoding="utf-8")

        duration_seconds = perf_counter() - started
        mark_batch_run_success(
            batch_run_id,
            duration_seconds=duration_seconds,
            article_count=len(articles),
            articles_file=articles_path.name,
            report_file=report_path.name,
        )
        logger.info(
            "event=batch_completed batch_run_id=%s status=success duration_seconds=%.2f "
            "article_count=%s report_file=%s",
            batch_run_id,
            duration_seconds,
            len(articles),
            report_path.name,
        )
        return BatchResult(
            batch_run_id=batch_run_id,
            article_count=len(articles),
            articles_path=articles_path,
            report_path=report_path,
        )
    except Exception as error:
        duration_seconds = perf_counter() - started
        try:
            mark_batch_run_failed(
                batch_run_id,
                duration_seconds=duration_seconds,
                error_message=str(error),
            )
        except Exception:
            # Preserve the original collection or analysis failure for the caller.
            logger.exception(
                "event=batch_failure_recording_failed batch_run_id=%s",
                batch_run_id,
            )
        logger.exception(
            "event=batch_completed batch_run_id=%s status=failed duration_seconds=%.2f",
            batch_run_id,
            duration_seconds,
        )
        raise


def main() -> None:
    run_batch()


if __name__ == "__main__":
    main()
