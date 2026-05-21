from __future__ import annotations

from eventradar.models import Article, Source
from eventradar.relevance import apply_source_context_entities, filter_relevant_articles


def _article(
    source: str,
    *,
    title: str = "sample",
    summary: str = "",
    matched_entities: dict[str, list[str]] | None = None,
) -> Article:
    return Article(
        title=title,
        link=f"https://example.com/{source}",
        summary=summary,
        published=None,
        source=source,
        category="event",
        matched_entities=matched_entities or {},
    )


def test_apply_source_context_entities_adds_event_source_signal() -> None:
    source = Source(
        name="Event Marketer",
        type="rss",
        url="https://www.eventmarketer.com/feed/",
    )

    [article] = apply_source_context_entities([_article("Event Marketer")], [source])

    assert article.matched_entities["SourceSignal"] == ["event_industry"]


def test_filter_relevant_articles_drops_error_and_broad_non_event_rows() -> None:
    sources = [
        Source(name="Billboard", type="rss", url="https://www.billboard.com/feed/"),
        Source(
            name="서울시 문화행사",
            type="javascript",
            url="https://www.seoul.go.kr/realmnews/culture/calendar.do",
        ),
        Source(name="예술의전당 공연", type="javascript", url="https://www.sac.or.kr"),
    ]
    articles = [
        _article(
            "Billboard", title="Artist profile", matched_entities={"Entertainment": ["artist"]}
        ),
        _article(
            "Billboard",
            title="Coachella setlist posted",
            matched_entities={"Entertainment": ["setlist"]},
        ),
        _article("서울시 문화행사", matched_entities={}),
        _article("예술의전당 공연", title="ERROR", summary="ERROR --> body"),
    ]

    filtered = filter_relevant_articles(articles, sources)

    assert [article.title for article in filtered] == [
        "Coachella setlist posted",
        "sample",
    ]
