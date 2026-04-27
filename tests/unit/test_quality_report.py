from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from eventradar.models import Article, CategoryConfig, Source
from eventradar.quality_report import build_quality_report, write_quality_report


def _article(
    source: str,
    *,
    published: datetime,
    matched_entities: dict[str, list[str]] | None = None,
) -> Article:
    return Article(
        title=f"{source} article",
        link=f"https://example.com/{source}",
        summary="event summary",
        published=published,
        source=source,
        category="event",
        matched_entities=matched_entities or {},
    )


def test_build_quality_report_tracks_event_source_statuses() -> None:
    generated_at = datetime(2026, 4, 13, tzinfo=UTC)
    category = CategoryConfig(
        category_name="event",
        display_name="Event",
        sources=[
            Source(
                name="서울시 문화행사",
                type="javascript",
                url="https://www.seoul.go.kr/realmnews/culture/calendar.do",
            ),
            Source(
                name="Ticketmaster Blog",
                type="rss",
                url="https://blog.ticketmaster.com/feed/",
            ),
            Source(
                name="Event Marketer",
                type="rss",
                url="https://www.eventmarketer.com/feed/",
            ),
            Source(name="Billboard", type="rss", url="https://www.billboard.com/feed/"),
            Source(
                name="Dormant Event Feed",
                type="rss",
                url="https://example.com/feed.xml",
                enabled=False,
                info_purpose=["official_event_calendar"],
                config={
                    "disabled_reason": "dormant_feed",
                    "required_before_enable": ["current_entries", "parser_smoke"],
                },
            ),
        ],
        entities=[],
    )
    articles = [
        _article(
            "서울시 문화행사",
            published=generated_at - timedelta(days=1),
            matched_entities={"SourceSignal": ["official_event_calendar"]},
        ),
        _article(
            "Ticketmaster Blog",
            published=generated_at - timedelta(hours=10),
            matched_entities={"SourceSignal": ["ticket_availability"]},
        ),
        _article(
            "Event Marketer",
            published=generated_at - timedelta(days=2),
            matched_entities={"SourceSignal": ["event_industry"]},
        ),
        _article(
            "Dormant Event Feed",
            published=generated_at - timedelta(hours=1),
            matched_entities={"SourceSignal": ["official_event_calendar"]},
        ),
    ]

    report = build_quality_report(
        category=category,
        articles=articles,
        quality_config={
            "data_quality": {
                "quality_outputs": {
                    "tracked_event_models": [
                        "official_event_calendar",
                        "ticket_availability",
                        "exhibitor_sponsor_signal",
                    ]
                },
                "freshness_sla": {
                    "official_event_calendar_days": 3,
                    "ticket_availability_hours": 24,
                    "exhibitor_sponsor_signal_days": 7,
                },
            }
        },
        generated_at=generated_at,
    )

    sources = {row["source"]: row for row in report["sources"]}
    assert report["summary"]["fresh_sources"] == 3
    assert report["summary"]["tracked_sources"] == 3
    assert report["summary"]["skipped_disabled_sources"] == 1
    assert report["summary"]["official_event_calendar_events"] == 1
    assert report["summary"]["ticket_availability_events"] == 1
    assert report["summary"]["exhibitor_sponsor_signal_events"] == 1
    assert sources["서울시 문화행사"]["status"] == "fresh"
    assert sources["Ticketmaster Blog"]["status"] == "fresh"
    assert sources["Event Marketer"]["status"] == "fresh"
    assert sources["Billboard"]["status"] == "not_tracked"
    assert sources["Dormant Event Feed"]["status"] == "skipped_disabled"
    assert sources["Dormant Event Feed"]["tracked"] is False
    assert sources["Dormant Event Feed"]["skip_reason"] == "dormant_feed"
    assert sources["Dormant Event Feed"]["reenable_gate"] == ["current_entries", "parser_smoke"]
    assert report["summary"]["event_occurrence_present_count"] == 1
    assert report["summary"]["daily_review_item_count"] == 3
    assert any(item["reason"] == "missing_required_fields" for item in report["daily_review_items"])
    assert any(item["reason"] == "missing_event_occurrence_id" for item in report["daily_review_items"])


def test_build_quality_report_extracts_event_contract_fields_and_reviews() -> None:
    generated_at = datetime(2026, 4, 13, 9, 0, tzinfo=UTC)
    category = CategoryConfig(
        category_name="event",
        display_name="Event",
        sources=[
            Source(
                name="서울시 문화행사",
                type="javascript",
                url="https://www.seoul.go.kr/realmnews/culture/calendar.do",
                trust_tier="T1_official",
                content_type="official_event_calendar",
                config={"venue_id": "seoul-city-culture", "city": "Seoul"},
            ),
            Source(
                name="인터파크 이벤트",
                type="javascript",
                url="https://ticket.interpark.com/TPGoodsList.asp?Ca=Eve",
                content_type="ticket_availability",
                config={"event_model": "ticket_availability"},
            ),
        ],
        entities=[],
    )
    official = _article(
        "서울시 문화행사",
        published=generated_at - timedelta(hours=2),
        matched_entities={"SourceSignal": ["official_event_calendar"]},
    )
    official.title = "서울 재즈 페스티벌"
    official.summary = (
        "Venue name: 서울광장. "
        "Event date: 2026-04-20. "
        "City: Seoul. "
        "Online: false."
    )
    ticket = _article(
        "인터파크 이벤트",
        published=generated_at - timedelta(hours=1),
        matched_entities={"SourceSignal": ["ticket_availability"]},
    )
    ticket.title = "서울 재즈 페스티벌 예매 오픈"
    ticket.summary = "Availability status: on_sale. Ticket open date: 2026-04-13T08:00:00+00:00."

    report = build_quality_report(
        category=category,
        articles=[official, ticket],
        quality_config={
            "data_quality": {
                "quality_outputs": {
                    "tracked_event_models": [
                        "official_event_calendar",
                        "ticket_availability",
                    ]
                }
            }
        },
        generated_at=generated_at,
    )

    official_event = report["events"][0]
    ticket_event = report["events"][1]
    assert official_event["venue_id"] == "seoul-city-culture"
    assert "seoul-city-culture" in official_event["event_occurrence_id"]
    assert ticket_event["availability_status"] == "on_sale"
    assert ticket_event["required_field_gaps"] == ["event_occurrence_id"]
    assert report["summary"]["event_required_field_gap_count"] == 1
    assert any(
        item["reason"] == "missing_required_fields"
        and item["event_model"] == "ticket_availability"
        for item in report["daily_review_items"]
    )


def test_write_quality_report_writes_latest_and_dated_json(tmp_path) -> None:
    report = {
        "category": "event",
        "generated_at": "2026-04-13T00:00:00+00:00",
        "summary": {},
        "sources": [],
    }

    paths = write_quality_report(report, output_dir=tmp_path, category_name="event")

    assert paths["latest"] == tmp_path / "event_quality.json"
    assert paths["dated"] == tmp_path / "event_20260413_quality.json"
    assert json.loads(paths["latest"].read_text(encoding="utf-8"))["category"] == "event"
