"""Collect headline articles from NAVER's Economy section."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable

import requests
from bs4 import BeautifulSoup, Tag

ECONOMY_SECTION_URL = "https://news.naver.com/section/101"
USER_AGENT = "Mozilla/5.0 (compatible; FinancialNewsBriefMVP/0.1)"


@dataclass(frozen=True)
class Article:
    id: str
    section_type: str
    display_position: int
    title: str
    description: str
    source: str
    url: str
    cluster_url: str | None
    related_count: int | None
    collected_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def fetch_economy_page(session: requests.Session | None = None) -> str:
    """Fetch the section page with a browser-like user agent."""
    client = session or requests.Session()
    response = client.get(
        ECONOMY_SECTION_URL,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9"},
        timeout=20,
    )
    response.raise_for_status()
    return response.text


def _text(node: Tag | None) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _article_id(url: str) -> str:
    """Use NAVER's oid/aid pair when present; otherwise use the URL itself."""
    parts = url.rstrip("/").split("/")
    if len(parts) >= 2 and parts[-1].isdigit() and parts[-2].isdigit():
        return f"{parts[-2]}-{parts[-1]}"
    return url


def _headline_items(soup: BeautifulSoup) -> Iterable[Tag]:
    # This is the currently rendered headline module, not the AiRS recommendation list.
    return soup.select("li._SECTION_HEADLINE")


def parse_headlines(html: str, limit: int = 10) -> list[Article]:
    """Extract the editorial headline cards and their metadata from section 101."""
    soup = BeautifulSoup(html, "html.parser")
    collected_at = datetime.now(timezone.utc).isoformat()
    articles: list[Article] = []
    seen_urls: set[str] = set()

    for item in _headline_items(soup):
        title_link = item.select_one("a.sa_text_title[href]")
        if not title_link:
            continue

        url = str(title_link["href"])
        if not url or url in seen_urls:
            continue

        title = _text(title_link)
        description = _text(item.select_one(".sa_text_lede"))
        source = _text(item.select_one(".sa_text_press"))
        cluster_link = item.select_one("a[href*='/cluster/']")
        count_node = item.select_one(".sa_text_cluster_num")
        related_count = int(_text(count_node)) if _text(count_node).isdigit() else None

        if not title or not source:
            continue

        seen_urls.add(url)
        articles.append(
            Article(
                id=_article_id(url),
                section_type="headline",
                display_position=len(articles) + 1,
                title=title,
                description=description,
                source=source,
                url=url,
                cluster_url=str(cluster_link["href"]) if cluster_link else None,
                related_count=related_count,
                collected_at=collected_at,
            )
        )
        if len(articles) >= limit:
            break

    if not articles:
        raise ValueError("헤드라인 기사를 찾지 못했습니다. 네이버 페이지 구조가 변경됐는지 확인하세요.")
    return articles


def collect_headlines(limit: int = 10) -> list[Article]:
    return parse_headlines(fetch_economy_page(), limit=limit)

