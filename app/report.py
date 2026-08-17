"""Render a structured brief as a portable Markdown report."""

from __future__ import annotations

from datetime import date
from typing import Sequence

from app.analyzer import Brief
from app.collector import Article

IMPORTANCE_LABEL = {"high": "높음", "medium": "보통", "low": "낮음"}


def render_markdown(brief: Brief, articles: Sequence[Article], report_date: date | None = None) -> str:
    by_id = {article.id: article for article in articles}
    lines = [
        f"# 경제 Morning Brief — {(report_date or date.today()).isoformat()}",
        "",
        "## 오늘의 한줄 요약",
        brief.overall_summary,
        "",
        "## 핵심 이슈",
    ]
    for index, issue in enumerate(brief.issues, start=1):
        lines.extend(
            [
                "",
                f"### {index}. {issue.keyword} · 중요도 {IMPORTANCE_LABEL[issue.importance]}",
                issue.summary,
                "",
                "관련 기사:",
            ]
        )
        for article_id in issue.related_article_ids:
            article = by_id[article_id]
            lines.append(f"- [{article.title}]({article.url}) — {article.source}")
    return "\n".join(lines) + "\n"

