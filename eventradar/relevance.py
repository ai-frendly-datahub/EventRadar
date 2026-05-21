from __future__ import annotations

from collections.abc import Iterable

from .models import Article, Source

CONTEXT_PURPOSES = {
    "culture_calendar",
    "event_industry",
    "exhibitor_sponsor_signal",
    "festival_calendar",
    "meeting_industry",
    "official_event_calendar",
    "ticket_availability",
    "venue_calendar",
}
STRONG_ENTITY_NAMES = {
    "Conference",
    "Event",
    "Exhibition",
    "Festival",
    "Meetup",
    "Performance",
}
EVENT_HINT_TERMS = {
    "coachella",
    "conference",
    "concert",
    "event",
    "expo",
    "festival",
    "showcase",
    "summit",
    "ticket",
    "tour",
    "venue",
    "공연",
    "박람회",
    "예매",
    "전시",
    "축제",
    "콘서트",
    "행사",
}
INVALID_PAGE_TERMS = {
    "404",
    "access denied",
    "error -->",
    "not found",
    "page not found",
    "service unavailable",
    "서비스 지연",
    "요청하신 페이지가 존재하지 않습니다",
    "페이지를 찾을수가 없습니다",
}


def apply_source_context_entities(
    articles: Iterable[Article],
    sources: Iterable[Source],
) -> list[Article]:
    source_map = {source.name: source for source in sources if source.enabled}
    classified: list[Article] = []
    for article in articles:
        source = source_map.get(article.source)
        if source is not None:
            tags = _source_context_tags(source)
            if tags:
                existing = article.matched_entities.get("SourceSignal", [])
                merged = sorted({str(value) for value in existing} | set(tags))
                article.matched_entities["SourceSignal"] = merged
        classified.append(article)
    return classified


def filter_relevant_articles(
    articles: Iterable[Article],
    sources: Iterable[Source],
) -> list[Article]:
    source_map = {source.name: source for source in sources if source.enabled}
    filtered: list[Article] = []
    for article in articles:
        source = source_map.get(article.source)
        if source is None or _is_invalid_page(article):
            continue
        if _source_context_tags(source) or _has_strong_event_signal(article):
            filtered.append(article)
    return filtered


def _has_strong_event_signal(article: Article) -> bool:
    if any(entity_name in STRONG_ENTITY_NAMES for entity_name in article.matched_entities):
        return True

    if "Entertainment" in article.matched_entities or "EventGeneral" in article.matched_entities:
        haystack = f"{article.title} {article.summary}".lower()
        return any(term in haystack for term in EVENT_HINT_TERMS)
    return False


def _is_invalid_page(article: Article) -> bool:
    title = (article.title or "").strip().lower()
    summary = (article.summary or "").strip().lower()
    if title == "error":
        return True
    return any(term in title or term in summary for term in INVALID_PAGE_TERMS)


def _source_context_tags(source: Source) -> list[str]:
    tags = {tag for tag in source.info_purpose if tag in CONTEXT_PURPOSES}
    source_name = source.name.lower()
    source_url = source.url.lower()
    content_type = source.content_type.lower()
    trust_tier = source.trust_tier.lower()

    if source.config.get("event_model"):
        tags.add(str(source.config["event_model"]))
    if content_type in CONTEXT_PURPOSES:
        tags.add(content_type)
    if source_name in {
        "exhibition news",
        "event marketer",
        "ufi blog",
        "museum next",
        "pcma convene",
        "event industry news",
        "exhibit city news",
        "smart meetings",
        "skift meetings",
        "iaee blog",
        "sched blog",
        "arts professional",
        "meetup blog",
    }:
        tags.add("event_industry")
    if source_name in {"iq magazine", "pollstar news", "ticketmaster blog"}:
        tags.add("ticket_availability")
    if "ticket" in source_name or "interpark" in source_url or "인터파크" in source.name:
        tags.add("ticket_availability")
    if trust_tier.startswith("t1") or any(
        token in source.name
        for token in (
            "강서구",
            "국립",
            "문화체육관광부",
            "서울시",
            "세종문화회관",
            "예술의전당",
            "지역축제",
            "한국관광공사",
        )
    ):
        tags.add("official_event_calendar")
    if any(token in source.name for token in ("국립", "세종문화회관", "예술의전당")):
        tags.add("venue_calendar")
    return sorted(tags)
