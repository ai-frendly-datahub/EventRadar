from __future__ import annotations

from eventradar.config_loader import load_category_config, load_category_quality_config


def test_load_category_config_preserves_source_metadata(tmp_path) -> None:
    categories_dir = tmp_path / "categories"
    categories_dir.mkdir()
    (categories_dir / "event.yaml").write_text(
        """
category_name: event
display_name: Event
sources:
  - name: Seoul Events
    id: seoul_events
    type: javascript
    url: https://example.com/events
    enabled: true
    language: ko
    country: KR
    trust_tier: T1_official
    weight: 2.0
    content_type: official_event_calendar
    collection_tier: C2_js
    producer_role: government
    info_purpose:
      - official_event_calendar
      - venue_calendar
    notes: official event calendar
    config:
      wait_for: .event_list
      event_model: official_event_calendar
entities: []
""",
        encoding="utf-8",
    )

    config = load_category_config("event", categories_dir=categories_dir)
    source = config.sources[0]

    assert source.id == "seoul_events"
    assert source.enabled is True
    assert source.language == "ko"
    assert source.country == "KR"
    assert source.trust_tier == "T1_official"
    assert source.weight == 2.0
    assert source.content_type == "official_event_calendar"
    assert source.collection_tier == "C2_js"
    assert source.producer_role == "government"
    assert source.info_purpose == ["official_event_calendar", "venue_calendar"]
    assert source.notes == "official event calendar"
    assert source.config == {
        "wait_for": ".event_list",
        "event_model": "official_event_calendar",
    }


def test_load_category_quality_config_exposes_event_contract(tmp_path) -> None:
    categories_dir = tmp_path / "categories"
    categories_dir.mkdir()
    (categories_dir / "event.yaml").write_text(
        """
category_name: event
display_name: Event
data_quality:
  priority: P1
  quality_outputs:
    freshness_report: reports/event_quality.json
    tracked_event_models:
      - official_event_calendar
      - ticket_availability
source_backlog:
  operational_candidates:
    - id: ticketmaster_discovery_api
sources: []
entities: []
""",
        encoding="utf-8",
    )

    metadata = load_category_quality_config("event", categories_dir=categories_dir)
    data_quality = metadata["data_quality"]
    source_backlog = metadata["source_backlog"]

    assert isinstance(data_quality, dict)
    assert data_quality["priority"] == "P1"
    assert data_quality["quality_outputs"]["freshness_report"] == "reports/event_quality.json"
    assert set(data_quality["quality_outputs"]["tracked_event_models"]) == {
        "official_event_calendar",
        "ticket_availability",
    }
    assert isinstance(source_backlog, dict)
    assert source_backlog["operational_candidates"][0]["id"] == "ticketmaster_discovery_api"
