"""feedparser *_parsed is UTC. time.mktime under TZ=Asia/Seoul stores it 9 hours early."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

from eventradar.collector import _extract_published
from eventradar.models import Article, Source
from eventradar.storage import RadarStorage

# 2026-10-28 15:00 UTC. tm_wday is Wednesday (2); tm_yday is 301.
_UTC_1500 = time.struct_time((2026, 10, 28, 15, 0, 0, 2, 301, 0))


def _seoul(monkeypatch) -> None:
    monkeypatch.setenv("TZ", "Asia/Seoul")
    time.tzset()


def _restore_tz(monkeypatch) -> None:
    monkeypatch.undo()
    time.tzset()


def test_feedparser_struct_stores_1500_utc_under_seoul(monkeypatch, tmp_path) -> None:
    _seoul(monkeypatch)
    try:
        shifted = datetime.fromtimestamp(time.mktime(_UTC_1500), tz=UTC)
        assert shifted == datetime(2026, 10, 28, 6, 0, tzinfo=UTC)

        published, raw = _extract_published({"published_parsed": _UTC_1500})
        assert raw is None
        assert published == datetime(2026, 10, 28, 15, 0, tzinfo=UTC)

        storage = RadarStorage(tmp_path / "radar.duckdb")
        try:
            storage.upsert_articles(
                [
                    Article(
                        title="Seoul concert",
                        link="https://example.com/concert",
                        summary="live",
                        published=published,
                        source="Example",
                        category="event",
                        published_raw=raw,
                    )
                ]
            )
            row = storage.conn.execute("SELECT published FROM articles").fetchone()
            assert row is not None
            assert row[0] == datetime(2026, 10, 28, 15, 0, tzinfo=UTC).replace(tzinfo=None)
        finally:
            storage.close()
    finally:
        _restore_tz(monkeypatch)


def test_offset_string_keeps_offset_and_zoneless_kr_uses_seoul() -> None:
    offset, offset_raw = _extract_published({"published": "Wed, 28 Oct 2026 15:00:00 +0900"})
    assert offset_raw == "Wed, 28 Oct 2026 15:00:00 +0900"
    assert offset is not None
    assert offset.utcoffset() == timedelta(hours=9)
    assert offset.astimezone(UTC) == datetime(2026, 10, 28, 6, 0, tzinfo=UTC)

    source = Source(name="행사", type="rss", url="https://calendar.example.kr/rss")
    zoneless, zoneless_raw = _extract_published(
        {"published": "2026-10-28 18:00:00"},
        source,
    )
    assert zoneless_raw == "2026-10-28 18:00:00"
    assert zoneless is not None
    assert zoneless.utcoffset() == timedelta(hours=9)
    assert zoneless.astimezone(UTC) == datetime(2026, 10, 28, 9, 0, tzinfo=UTC)

    configured = Source(
        name="dotcom",
        type="rss",
        url="https://events.example.com/feed",
        config={"default_timezone": "Asia/Seoul"},
    )
    from_config, _ = _extract_published({"published": "2026-10-28 18:00:00"}, configured)
    assert from_config is not None
    assert from_config.astimezone(UTC) == datetime(2026, 10, 28, 9, 0, tzinfo=UTC)
