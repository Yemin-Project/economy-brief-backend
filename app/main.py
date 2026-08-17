"""Run the MVP: collect NAVER Economy headlines, analyze them, save a report."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from app.analyzer import analyze_articles
from app.collector import collect_headlines
from app.report import render_markdown

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


@dataclass(frozen=True)
class BatchResult:
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
    print("경제 섹션 헤드라인을 수집합니다...")
    articles = collect_headlines(limit=10)
    print(f"헤드라인 {len(articles)}건을 수집했습니다.")

    print("LLM으로 경제 브리프를 생성합니다...")
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
    print(f"완료: {report_path}")
    return BatchResult(
        article_count=len(articles),
        articles_path=articles_path,
        report_path=report_path,
    )


def main() -> None:
    run_batch()


if __name__ == "__main__":
    main()
