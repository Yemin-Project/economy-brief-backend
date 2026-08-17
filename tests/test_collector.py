from app.collector import parse_headlines


HTML = """
<ul>
  <li class="sa_item _SECTION_HEADLINE">
    <a class="sa_text_title" href="https://n.news.naver.com/mnews/article/001/001234567">첫 번째 기사</a>
    <div class="sa_text_lede">첫 번째 설명문</div>
    <div class="sa_text_press">연합뉴스</div>
    <a href="/cluster/example"><span class="sa_text_cluster_num">3</span></a>
  </li>
  <li class="sa_item _SECTION_HEADLINE">
    <a class="sa_text_title" href="https://n.news.naver.com/mnews/article/002/001234568">두 번째 기사</a>
    <div class="sa_text_lede">두 번째 설명문</div>
    <div class="sa_text_press">뉴스원</div>
  </li>
</ul>
"""


def test_parse_headlines_extracts_only_headline_cards() -> None:
    articles = parse_headlines(HTML)

    assert [article.id for article in articles] == ["001-001234567", "002-001234568"]
    assert articles[0].related_count == 3
    assert articles[0].section_type == "headline"
    assert articles[1].display_position == 2

