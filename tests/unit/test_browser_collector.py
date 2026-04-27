from __future__ import annotations

from eventradar.browser_collector import collect_browser_sources
from eventradar.models import Source


def test_collect_browser_sources_forwards_source_config(monkeypatch) -> None:
    import eventradar.browser_collector as module

    source = Source(
        name="서울시 문화행사",
        type="javascript",
        url="https://www.seoul.go.kr/realmnews/culture/calendar.do",
        config={"wait_for": ".event_list"},
    )
    captured: dict[str, object] = {}

    def fake_collect(*, sources, category, timeout, health_db_path):
        captured["sources"] = sources
        captured["category"] = category
        captured["timeout"] = timeout
        captured["health_db_path"] = health_db_path
        return [], []

    monkeypatch.setattr(module, "_BROWSER_COLLECTION_AVAILABLE", True)
    monkeypatch.setattr(module, "_core_collect", fake_collect)

    articles, errors = collect_browser_sources([source], "event")

    assert articles == []
    assert errors == []
    assert captured["category"] == "event"
    assert captured["sources"] == [
        {
            "name": "서울시 문화행사",
            "type": "javascript",
            "url": "https://www.seoul.go.kr/realmnews/culture/calendar.do",
            "config": {"wait_for": ".event_list"},
        }
    ]
