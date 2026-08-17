"""Turn collected headline metadata into a structured economic brief."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Sequence

from openai import OpenAI

from app.collector import Article

REPORT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "overall_summary": {"type": "string"},
        "issues": {
            "type": "array",
            "minItems": 1,
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "keyword": {"type": "string"},
                    "importance": {"type": "string", "enum": ["high", "medium", "low"]},
                    "summary": {"type": "string"},
                    "related_article_ids": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                },
                "required": ["keyword", "importance", "summary", "related_article_ids"],
            },
        },
    },
    "required": ["overall_summary", "issues"],
}

SYSTEM_PROMPT = """당신은 한국 경제 뉴스 브리핑 편집자입니다.
입력은 네이버 뉴스 경제 섹션의 헤드라인 기사 목록입니다.

규칙:
- 제목과 설명문에 명시된 정보만 사용하고, 기사에 없는 사실·수치·전망을 만들지 마세요.
- 같은 사건 또는 흐름을 다룬 기사는 하나의 이슈로 묶으세요.
- 투자 매수·매도 추천을 하지 마세요.
- 헤드라인은 편집상 중요도가 있으므로 이슈 우선순위에 반영하세요.
- overall_summary는 반드시 정확히 4개의 완결된 한국어 문장으로 작성하세요. 핵심 흐름과 배경을 포함하세요.
- 각 issue summary는 반드시 정확히 4개의 완결된 한국어 문장으로 작성하세요. 기사에 드러난 배경, 핵심 내용, 영향 또는 다음 확인 사항을 포함하세요.
- 영향 또는 다음 확인 사항은 입력 기사에 근거가 있을 때만 작성하세요.
- 각 문장은 입력 기사에서 확인되는 구체적 사실(주체, 시점, 수치, 배경, 조치)을 사용해 내용을 보강하세요.
- "향후 확인할 필요가 있다", "주목할 필요가 있다"처럼 새 정보가 없는 일반적인 문장으로 분량을 채우지 마세요.
- related_article_ids에는 입력에 있는 ID만 넣으세요.
"""


@dataclass(frozen=True)
class Issue:
    keyword: str
    importance: str
    summary: str
    related_article_ids: list[str]


@dataclass(frozen=True)
class Brief:
    overall_summary: str
    issues: list[Issue]


def analyze_articles(articles: Sequence[Article], model: str | None = None) -> Brief:
    """Call the Responses API and require the report JSON schema."""
    if not articles:
        raise ValueError("분석할 기사가 없습니다.")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY가 없습니다. .env 파일을 만들고 키를 설정하세요.")

    payload = {"articles": [asdict(article) for article in articles]}
    client = OpenAI()
    response = client.responses.create(
        model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "다음 기사 목록으로 오늘의 경제 브리프를 생성하세요.\n"
                + json.dumps(payload, ensure_ascii=False),
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "economic_morning_brief",
                "strict": True,
                "schema": REPORT_SCHEMA,
            }
        },
    )
    try:
        data = json.loads(response.output_text)
    except json.JSONDecodeError as error:
        raise RuntimeError("LLM 응답이 올바른 JSON이 아닙니다.") from error

    valid_ids = {article.id for article in articles}
    issues = []
    for issue in data["issues"]:
        article_ids = [article_id for article_id in issue["related_article_ids"] if article_id in valid_ids]
        if article_ids:
            issues.append(Issue(**{**issue, "related_article_ids": article_ids}))
    if not issues:
        raise RuntimeError("LLM이 유효한 관련 기사 ID를 반환하지 않았습니다.")
    return Brief(overall_summary=data["overall_summary"], issues=issues)
