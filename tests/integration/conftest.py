from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from eventradar.models import Article, CategoryConfig, EntityDefinition, Source
from eventradar.storage import RadarStorage


@pytest.fixture
def tmp_storage(tmp_path: Path) -> RadarStorage:
    """Create a temporary RadarStorage instance for testing."""
    db_path = tmp_path / "test.duckdb"
    storage = RadarStorage(db_path)
    yield storage
    storage.close()


@pytest.fixture
def sample_articles() -> list[Article]:
    """Create sample articles with realistic event domain data."""
    now = datetime.now(timezone.utc)
    return [
        Article(
            title="2024 서울 뮤직 페스티벌 개최",
            link="https://event.example.com/music-festival-2024",
            summary="올해 서울 뮤직 페스티벌이 개최됩니다. 유명 아티스트들이 참여합니다.",
            published=now,
            source="event_portal",
            category="event",
            matched_entities={},
        ),
        Article(
            title="국립미술관 특별전시 '현대미술의 흐름'",
            link="https://event.example.com/art-exhibition-2024",
            summary="국립미술관에서 현대미술 특별전시가 열립니다. 국내외 작가 50명 참여.",
            published=now,
            source="event_portal",
            category="event",
            matched_entities={},
        ),
        Article(
            title="K-POP 콘서트 시리즈 티켓 오픈",
            link="https://event.example.com/kpop-concert-2024",
            summary="유명 K-POP 그룹의 콘서트 티켓이 오픈되었습니다.",
            published=now,
            source="event_portal",
            category="event",
            matched_entities={},
        ),
        Article(
            title="서울 국제 영화제 개최 안내",
            link="https://event.example.com/film-festival-2024",
            summary="서울 국제 영화제가 개최됩니다. 세계 각국의 영화가 상영됩니다.",
            published=now,
            source="event_portal",
            category="event",
            matched_entities={},
        ),
        Article(
            title="2024 서울 마라톤 대회 참가 신청",
            link="https://event.example.com/marathon-2024",
            summary="서울 마라톤 대회 참가 신청이 시작되었습니다.",
            published=now,
            source="event_portal",
            category="event",
            matched_entities={},
        ),
    ]


@pytest.fixture
def sample_entities() -> list[EntityDefinition]:
    """Create sample entities with event domain keywords."""
    return [
        EntityDefinition(
            name="music_event",
            display_name="음악 행사",
            keywords=["콘서트", "뮤직", "페스티벌", "공연", "아티스트"],
        ),
        EntityDefinition(
            name="art_exhibition",
            display_name="미술 전시",
            keywords=["전시", "미술관", "갤러리", "작품", "전시회"],
        ),
        EntityDefinition(
            name="film_festival",
            display_name="영화제",
            keywords=["영화제", "영화", "영화관", "상영", "시네마"],
        ),
        EntityDefinition(
            name="sports_event",
            display_name="스포츠 행사",
            keywords=["마라톤", "스포츠", "경기", "대회", "운동"],
        ),
        EntityDefinition(
            name="seminar",
            display_name="세미나",
            keywords=["세미나", "강연", "워크숍", "교육", "강좌"],
        ),
    ]


@pytest.fixture
def sample_config(tmp_path: Path, sample_entities: list[EntityDefinition]) -> CategoryConfig:
    """Create a sample CategoryConfig for testing."""
    sources = [
        Source(
            name="event_portal",
            type="rss",
            url="https://event.example.com/feed",
        ),
    ]
    return CategoryConfig(
        category_name="event",
        display_name="이벤트",
        sources=sources,
        entities=sample_entities,
    )
