"""Run the MVP: collect NAVER Economy headlines, analyze them, save a report."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app.analyzer import analyze_articles
from app.collector import collect_headlines
from app.report import render_markdown

OUTPUT_DIR = Path("outputs")


def main() -> None:
    load_dotenv()
    print("경제 섹션 헤드라인을 수집합니다...")
    articles = collect_headlines(limit=10)
    print(f"헤드라인 {len(articles)}건을 수집했습니다.")

    print("LLM으로 경제 브리프를 생성합니다...")
    brief = analyze_articles(articles)
    report = render_markdown(brief, articles)

    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (OUTPUT_DIR / f"articles_{timestamp}.json").write_text(
        json.dumps([article.to_dict() for article in articles], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report_path = OUTPUT_DIR / f"morning_brief_{timestamp}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"완료: {report_path}")


if __name__ == "__main__":
    main()

