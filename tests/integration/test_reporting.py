from __future__ import annotations

import json
from pathlib import Path

import pytest

from eventradar.models import Article, EntityDefinition
from eventradar.reporter import generate_report


def _apply_entity_rules_py39(
    articles: list[Article], entities: list[EntityDefinition]
) -> list[Article]:
    """Apply entity rules (Python 3.9 compatible version)."""
    analyzed: list[Article] = []
    lowered_entities = [
        EntityDefinition(
            name=e.name,
            display_name=e.display_name,
            keywords=[kw.lower() for kw in e.keywords],
        )
        for e in entities
    ]

    for article in articles:
        haystack = f"{article.title}\n{article.summary}".lower()
        matches: dict[str, list[str]] = {}
        for entity, lowered_entity in zip(entities, lowered_entities, strict=False):
            hit_keywords = [kw for kw in lowered_entity.keywords if kw and kw in haystack]
            if hit_keywords:
                matches[entity.name] = hit_keywords
        article.matched_entities = matches
        analyzed.append(article)

    return analyzed


def test_report_generation_includes_event_quality_panel(
    tmp_path: Path,
    sample_articles: list[Article],
    sample_config,
) -> None:
    output_path = tmp_path / "quality_report.html"

    result = generate_report(
        category=sample_config,
        articles=sample_articles[:1],
        output_path=output_path,
        stats={"total_articles": 1, "sources": 1},
        quality_report={
            "summary": {
                "official_event_calendar_events": 1,
                "ticket_availability_events": 0,
                "venue_calendar_events": 0,
                "exhibitor_sponsor_signal_events": 0,
                "event_occurrence_present_count": 1,
                "event_required_field_gap_count": 1,
                "fresh_sources": 1,
                "missing_sources": 0,
                "daily_review_item_count": 1,
            },
            "sources": [],
            "events": [
                {
                    "event_model": "official_event_calendar",
                    "source": "sample",
                    "title": "sample event",
                    "event_occurrence_id": "sample:event",
                }
            ],
            "daily_review_items": [
                {
                    "reason": "missing_required_fields",
                    "event_model": "ticket_availability",
                    "source": "sample",
                    "required_field_gaps": ["availability_status"],
                }
            ],
        },
    )

    content = result.read_text(encoding="utf-8")
    assert 'id="event-quality"' in content
    assert "official_event_calendar" in content
    assert "missing_required_fields" in content

    summaries = sorted(tmp_path.glob("event_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_summary.json"))
    assert len(summaries) == 1
    summary = json.loads(summaries[0].read_text(encoding="utf-8"))
    assert summary["ontology"]["repo"] == "EventRadar"
    assert summary["ontology"]["ontology_version"] == "0.1.0"
    assert "event.official_event_calendar" in summary["ontology"]["event_model_ids"]


def test_report_generation_normalizes_source_tabs(
    tmp_path: Path,
    sample_config,
) -> None:
    output_path = tmp_path / "normalized_report.html"
    article = Article(
        title="Event\tTitle",
        link="https://example.com/event",
        summary="Summary\twith\tspacing",
        published=None,
        source="sample",
        category="event",
    )

    result = generate_report(
        category=sample_config,
        articles=[article],
        output_path=output_path,
        stats={"total_articles": 1, "sources": 1},
        quality_report={
            "summary": {},
            "sources": [],
            "events": [
                {
                    "event_model": "official_event_calendar",
                    "source": "sample",
                    "title": "Quality\tTitle",
                    "event_occurrence_id": "sample:event",
                }
            ],
            "daily_review_items": [
                {
                    "reason": "source_attention",
                    "event_model": "official_event_calendar",
                    "source": "sample",
                    "detail": "Detail\twith\tspacing",
                }
            ],
        },
    )

    content = result.read_text(encoding="utf-8")
    assert "Event Title" in content
    assert "Quality Title" in content
    assert "Detail with spacing" in content
    assert "\t" not in content


@pytest.mark.integration
def test_report_generation(
    tmp_path: Path,
    sample_articles: list[Article],
    sample_entities: list[EntityDefinition],
    sample_config,
) -> None:
    """Test report generation: generate HTML → verify file exists + contains expected content."""
    analyzed = _apply_entity_rules_py39(sample_articles, sample_entities)

    output_path = tmp_path / "report.html"
    stats = {"total_articles": len(analyzed), "sources": 1}

    result = generate_report(
        category=sample_config,
        articles=analyzed,
        output_path=output_path,
        stats=stats,
        quality_report={
            "summary": {
                "official_event_calendar_events": 1,
                "ticket_availability_events": 1,
                "venue_calendar_events": 0,
                "exhibitor_sponsor_signal_events": 0,
                "event_occurrence_present_count": 2,
                "event_required_field_gap_count": 0,
                "fresh_sources": 1,
                "missing_sources": 0,
                "daily_review_item_count": 0,
            },
            "sources": [],
            "events": [
                {
                    "event_model": "official_event_calendar",
                    "source": "sample",
                    "title": "sample event",
                    "event_occurrence_id": "sample:event",
                }
            ],
            "daily_review_items": [],
        },
    )

    assert result.exists()
    assert result.suffix == ".html"

    content = result.read_text(encoding="utf-8")
    assert "이벤트" in content
    assert "2024 서울 뮤직 페스티벌" in content
    assert "국립미술관" in content
