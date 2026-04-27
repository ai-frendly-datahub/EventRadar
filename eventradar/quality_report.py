from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import Article, CategoryConfig, Source


TRACKED_EVENT_MODEL_ORDER = [
    "official_event_calendar",
    "ticket_availability",
    "venue_calendar",
    "exhibitor_sponsor_signal",
]
TRACKED_EVENT_MODELS = set(TRACKED_EVENT_MODEL_ORDER)
EVENT_DATE_LABELS = ("Event date", "Event start date", "Start date", "Published date")
TICKET_DATE_LABELS = ("Ticket open date", "On sale date", "Observed at")
SUMMARY_LABELS = (
    "Availability status",
    "City",
    "Country",
    "Event date",
    "Event start date",
    "Event title",
    "Exhibitor",
    "Location",
    "Online",
    "On sale date",
    "Organization",
    "Organization name",
    "Published date",
    "Signal type",
    "Sponsor",
    "Start date",
    "Ticket open date",
    "Venue",
    "Venue ID",
    "Venue name",
)


def build_quality_report(
    *,
    category: CategoryConfig,
    articles: Iterable[Article],
    errors: Iterable[str] | None = None,
    quality_config: Mapping[str, object] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated = _as_utc(generated_at or datetime.now(UTC))
    articles_list = list(articles)
    errors_list = [str(error) for error in (errors or [])]
    quality = _dict(quality_config or {}, "data_quality")
    freshness_sla = _dict(quality, "freshness_sla")
    tracked_event_models = _tracked_event_models(quality)

    event_rows = _build_event_rows(articles_list, category.sources, tracked_event_models)
    source_rows = [
        _build_source_row(
            source=source,
            articles=articles_list,
            event_rows=event_rows,
            errors=errors_list,
            freshness_sla=freshness_sla,
            tracked_event_models=tracked_event_models,
            generated_at=generated,
        )
        for source in category.sources
    ]

    status_counts = Counter(str(row["status"]) for row in source_rows)
    event_counts = Counter(str(row["event_model"]) for row in event_rows)
    summary = {
        "total_sources": len(source_rows),
        "enabled_sources": sum(1 for row in source_rows if row["enabled"]),
        "tracked_sources": sum(1 for row in source_rows if row["tracked"]),
        "fresh_sources": status_counts.get("fresh", 0),
        "stale_sources": status_counts.get("stale", 0),
        "missing_sources": status_counts.get("missing", 0),
        "missing_event_sources": status_counts.get("missing_event", 0),
        "unknown_event_date_sources": status_counts.get("unknown_event_date", 0),
        "not_tracked_sources": status_counts.get("not_tracked", 0),
        "skipped_disabled_sources": status_counts.get("skipped_disabled", 0),
        "collection_error_count": len(errors_list),
    }
    for event_model in TRACKED_EVENT_MODEL_ORDER:
        summary[f"{event_model}_events"] = event_counts.get(event_model, 0)
    summary.update(_event_quality_summary(event_rows))
    daily_review_items = _daily_review_items(event_rows, source_rows)
    summary["daily_review_item_count"] = len(daily_review_items)

    return {
        "category": category.category_name,
        "generated_at": generated.isoformat(),
        "scope_note": (
            "Official calendars, venue pages, ticket pages, and event-industry sources "
            "are tracked separately from broad culture/entertainment news. Generic error "
            "pages and broad rows without event-domain signals are excluded from reports."
        ),
        "summary": summary,
        "sources": source_rows,
        "events": event_rows,
        "daily_review_items": daily_review_items,
        "quality_gates": list(quality.get("quality_gates", []))
        if isinstance(quality.get("quality_gates"), list)
        else [],
        "source_backlog": (quality_config or {}).get("source_backlog", {}),
        "errors": errors_list,
    }


def write_quality_report(
    report: Mapping[str, object],
    *,
    output_dir: Path,
    category_name: str,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = _parse_datetime(str(report.get("generated_at") or "")) or datetime.now(UTC)
    date_stamp = _as_utc(generated_at).strftime("%Y%m%d")
    latest_path = output_dir / f"{category_name}_quality.json"
    dated_path = output_dir / f"{category_name}_{date_stamp}_quality.json"
    encoded = json.dumps(report, ensure_ascii=False, indent=2, default=str)
    latest_path.write_text(encoded + "\n", encoding="utf-8")
    dated_path.write_text(encoded + "\n", encoding="utf-8")
    return {"latest": latest_path, "dated": dated_path}


def _build_event_rows(
    articles: list[Article],
    sources: list[Source],
    tracked_event_models: set[str],
) -> list[dict[str, Any]]:
    source_map = {source.name: source for source in sources}
    rows: list[dict[str, Any]] = []
    for article in articles:
        source = source_map.get(article.source)
        if source is None or not source.enabled:
            continue
        event_model = _source_event_model(source)
        if event_model not in tracked_event_models:
            continue
        event_at = (
            _as_utc(article.published or article.collected_at)
            if (article.published or article.collected_at)
            else None
        )
        rows.append(_event_row(article=article, source=source, event_model=event_model, event_at=event_at))
    return rows


def _event_row(
    *,
    article: Article,
    source: Source,
    event_model: str,
    event_at: datetime | None,
) -> dict[str, Any]:
    event_title = article.title.strip() or _summary_value(article.summary, "Event title")
    venue_name = _first_non_empty(
        _summary_value(article.summary, "Venue name"),
        _summary_value(article.summary, "Venue"),
        _source_venue_name(source),
    )
    city = _first_non_empty(
        _summary_value(article.summary, "City"),
        _summary_value(article.summary, "Location"),
        _string_value(source.config.get("city")),
        "Seoul" if "서울" in source.name else "",
    )
    country = _first_non_empty(
        _summary_value(article.summary, "Country"),
        _string_value(source.config.get("country")),
        "KR" if "한국" in source.name or "서울" in source.name else "",
    )
    online_flag = _online_flag(
        _first_non_empty(
            _summary_value(article.summary, "Online"),
            _string_value(source.config.get("online_flag")),
        )
    )
    event_date = _first_non_empty(
        *(_summary_value(article.summary, label) for label in EVENT_DATE_LABELS),
        event_at.isoformat() if event_at else "",
    )
    ticket_open_date = _first_non_empty(
        *(_summary_value(article.summary, label) for label in TICKET_DATE_LABELS),
        event_at.isoformat() if event_model == "ticket_availability" and event_at else "",
    )
    source_url = article.link
    venue_id = _first_non_empty(
        _summary_value(article.summary, "Venue ID"),
        _string_value(source.config.get("venue_id")),
        _slug(venue_name)
        if venue_name and event_model in {"official_event_calendar", "venue_calendar"}
        else "",
    )
    event_occurrence_id = _event_occurrence_id(
        event_title=event_title,
        venue_id=venue_id,
        event_date=event_date,
        city=city,
        online_flag=online_flag,
    )
    availability_status = _availability_status(article)
    organization_name = _first_non_empty(
        _summary_value(article.summary, "Organization"),
        _summary_value(article.summary, "Organization name"),
        _summary_value(article.summary, "Sponsor"),
        _summary_value(article.summary, "Exhibitor"),
    )
    signal_type = _first_non_empty(
        _summary_value(article.summary, "Signal type"),
        _signal_type(article),
    )
    row = {
        "source": article.source,
        "event_model": event_model,
        "title": article.title,
        "event_title": event_title,
        "url": article.link,
        "source_url": source_url,
        "event_at": event_at.isoformat() if event_at else None,
        "event_date": event_date or None,
        "ticket_open_date": ticket_open_date or None,
        "venue_id": venue_id,
        "venue_name": venue_name,
        "city": city,
        "country": country,
        "online_flag": online_flag,
        "event_occurrence_id": event_occurrence_id,
        "availability_status": availability_status,
        "organization_name": organization_name,
        "signal_type": signal_type,
        "conference": _matches(article, "Conference"),
        "exhibition": _matches(article, "Exhibition"),
        "festival": _matches(article, "Festival"),
        "performance": _matches(article, "Performance"),
        "meetup": _matches(article, "Meetup"),
        "source_signal": _matches(article, "SourceSignal"),
    }
    row["required_field_gaps"] = _required_field_gaps(row, event_model)
    return row


def _build_source_row(
    *,
    source: Source,
    articles: list[Article],
    event_rows: list[dict[str, Any]],
    errors: list[str],
    freshness_sla: Mapping[str, object],
    tracked_event_models: set[str],
    generated_at: datetime,
) -> dict[str, Any]:
    source_articles = [article for article in articles if article.source == source.name]
    source_errors = [error for error in errors if error.startswith(f"{source.name}:")]
    event_model = _source_event_model(source)
    source_event_rows = [
        row
        for row in event_rows
        if row["source"] == source.name and row["event_model"] == event_model
    ]
    latest_event = _latest_event(source_event_rows)
    latest_event_at = _parse_datetime(str(latest_event.get("event_at") or "")) if latest_event else None
    sla_days = _source_sla_days(source, event_model, freshness_sla)
    age_days = _age_days(generated_at, latest_event_at) if latest_event_at else None
    disabled_reason = _string_value(source.config.get("disabled_reason"))
    reenable_gate = _list_value(source.config.get("required_before_enable"))
    status = _source_status(
        source=source,
        event_model=event_model,
        tracked_event_models=tracked_event_models,
        article_count=len(source_articles),
        event_count=len(source_event_rows),
        latest_event_at=latest_event_at,
        sla_days=sla_days,
        age_days=age_days,
    )

    return {
        "source": source.name,
        "source_type": source.type,
        "enabled": source.enabled,
        "trust_tier": source.trust_tier,
        "content_type": source.content_type,
        "collection_tier": source.collection_tier,
        "producer_role": source.producer_role,
        "info_purpose": source.info_purpose,
        "tracked": source.enabled and event_model in tracked_event_models,
        "event_model": event_model,
        "freshness_sla_days": sla_days,
        "status": status,
        "skip_reason": disabled_reason if not source.enabled else "",
        "reenable_gate": reenable_gate if not source.enabled else [],
        "article_count": len(source_articles),
        "event_count": len(source_event_rows),
        "latest_event_at": latest_event_at.isoformat() if latest_event_at else None,
        "age_days": round(age_days, 2) if age_days is not None else None,
        "latest_title": str(latest_event.get("title", "")) if latest_event else "",
        "latest_url": str(latest_event.get("url", "")) if latest_event else "",
        "latest_source_signal": latest_event.get("source_signal", []) if latest_event else [],
        "latest_event_occurrence_id": latest_event.get("event_occurrence_id", "")
        if latest_event
        else "",
        "latest_required_field_gaps": latest_event.get("required_field_gaps", [])
        if latest_event
        else [],
        "errors": source_errors,
    }


def _source_status(
    *,
    source: Source,
    event_model: str,
    tracked_event_models: set[str],
    article_count: int,
    event_count: int,
    latest_event_at: datetime | None,
    sla_days: float | None,
    age_days: float | None,
) -> str:
    if not source.enabled:
        return "skipped_disabled"
    if event_model not in tracked_event_models:
        return "not_tracked"
    if article_count == 0:
        return "missing"
    if event_count == 0:
        return "missing_event"
    if latest_event_at is None or age_days is None:
        return "unknown_event_date"
    if sla_days is not None and age_days > sla_days:
        return "stale"
    return "fresh"


def _tracked_event_models(quality: Mapping[str, object]) -> set[str]:
    outputs = _dict(quality, "quality_outputs")
    raw = outputs.get("tracked_event_models")
    if isinstance(raw, list):
        values = {str(item).strip() for item in raw if str(item).strip()}
        return values & TRACKED_EVENT_MODELS or set(TRACKED_EVENT_MODELS)
    return set(TRACKED_EVENT_MODELS)


def _source_event_model(source: Source) -> str:
    raw = source.config.get("event_model")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    purposes = set(source.info_purpose)
    if "ticket_availability" in purposes:
        return "ticket_availability"
    if "venue_calendar" in purposes:
        return "venue_calendar"
    if "official_event_calendar" in purposes:
        return "official_event_calendar"
    if "exhibitor_sponsor_signal" in purposes:
        return "exhibitor_sponsor_signal"

    source_name = source.name.lower()
    source_url = source.url.lower()
    if "ticket" in source_name or "interpark" in source_url or "인터파크" in source.name:
        return "ticket_availability"
    if any(token in source.name for token in ("국립", "세종문화회관", "예술의전당", "강서구")):
        return "venue_calendar"
    if source.trust_tier.lower().startswith("t1") or any(
        token in source.name
        for token in ("문화체육관광부", "서울시", "지역축제", "한국관광공사")
    ):
        return "official_event_calendar"
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
        return "exhibitor_sponsor_signal"
    return ""


def _source_sla_days(
    source: Source,
    event_model: str,
    freshness_sla: Mapping[str, object],
) -> float | None:
    raw_source_sla = source.config.get("freshness_sla_days")
    parsed_source_sla = _as_float(raw_source_sla)
    if parsed_source_sla is not None:
        return parsed_source_sla

    by_key = freshness_sla.get(event_model)
    if isinstance(by_key, Mapping):
        return _as_float(by_key.get("max_age_days"))

    suffixed_days = _as_float(freshness_sla.get(f"{event_model}_days"))
    if suffixed_days is not None:
        return suffixed_days

    suffixed_hours = _as_float(freshness_sla.get(f"{event_model}_hours"))
    if suffixed_hours is not None:
        return suffixed_hours / 24
    return None


def _latest_event(event_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    dated: list[tuple[datetime, dict[str, Any]]] = []
    undated: list[dict[str, Any]] = []
    for row in event_rows:
        event_at = _parse_datetime(str(row.get("event_at") or ""))
        if event_at is not None:
            dated.append((event_at, row))
        else:
            undated.append(row)
    if dated:
        return max(dated, key=lambda item: item[0])[1]
    return undated[0] if undated else None


def _event_quality_summary(event_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "event_occurrence_present_count": sum(
            1 for row in event_rows if row.get("event_occurrence_id")
        ),
        "venue_id_present_count": sum(1 for row in event_rows if row.get("venue_id")),
        "availability_status_present_count": sum(
            1 for row in event_rows if row.get("availability_status")
        ),
        "organization_signal_present_count": sum(
            1 for row in event_rows if row.get("organization_name")
        ),
        "event_required_field_gap_count": sum(
            len(_list_value(row.get("required_field_gaps"))) for row in event_rows
        ),
    }


def _daily_review_items(
    event_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    review_items: list[dict[str, Any]] = []
    for row in event_rows:
        gaps = _list_value(row.get("required_field_gaps"))
        if gaps:
            review_items.append(
                {
                    "reason": "missing_required_fields",
                    "event_model": row.get("event_model"),
                    "source": row.get("source"),
                    "title": row.get("title"),
                    "event_occurrence_id": row.get("event_occurrence_id"),
                    "required_field_gaps": gaps,
                }
            )
        if row.get("event_model") in {
            "official_event_calendar",
            "ticket_availability",
            "venue_calendar",
        } and not row.get("event_occurrence_id"):
            review_items.append(
                {
                    "reason": "missing_event_occurrence_id",
                    "event_model": row.get("event_model"),
                    "source": row.get("source"),
                    "title": row.get("title"),
                }
            )

    for row in source_rows:
        status = str(row.get("status") or "")
        if status in {"missing", "missing_event", "stale", "unknown_event_date"}:
            review_items.append(
                {
                    "reason": "source_attention",
                    "event_model": row.get("event_model"),
                    "source": row.get("source"),
                    "status": status,
                    "detail": row.get("latest_title") or row.get("latest_url") or "",
                }
            )

    tracked_models = {
        str(row.get("event_model") or "")
        for row in source_rows
        if row.get("enabled") and row.get("tracked")
    }
    observed_models = {str(row.get("event_model") or "") for row in event_rows}
    for event_model in sorted(model for model in tracked_models if model and model not in observed_models):
        affected_sources = [
            str(row.get("source") or "")
            for row in source_rows
            if row.get("enabled") and row.get("event_model") == event_model
        ]
        review_items.append(
            {
                "reason": "missing_tracked_event_layer",
                "event_model": event_model,
                "source": ", ".join(affected_sources[:3]),
            }
        )
    return review_items[:50]


def _matches(article: Article, key: str) -> list[str]:
    values = article.matched_entities.get(key, [])
    if isinstance(values, list):
        return [str(value) for value in values]
    return []


def _dict(mapping: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = mapping.get(key)
    return value if isinstance(value, Mapping) else {}


def _list_value(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _summary_value(summary: str, label: str) -> str:
    text = summary or ""
    marker = f"{label}:"
    start = text.find(marker)
    if start < 0:
        return ""
    value_start = start + len(marker)
    next_positions = [
        pos
        for other_label in SUMMARY_LABELS
        if other_label != label
        for pos in [text.find(f" {other_label}:", value_start)]
        if pos >= 0
    ]
    value_end = min(next_positions) if next_positions else len(text)
    return text[value_start:value_end].strip().rstrip(".").strip()


def _source_venue_name(source: Source) -> str:
    explicit = _string_value(source.config.get("venue_name"))
    if explicit:
        return explicit
    cleaned = source.name
    for suffix in (" 행사", " 문화행사", " 공연", " 전시", " 이벤트", " 축제정보"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    return cleaned


def _string_value(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _online_flag(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "online", "virtual", "y"}:
        return True
    if normalized in {"false", "0", "no", "offline", "onsite", "n"}:
        return False
    return None


def _availability_status(article: Article) -> str:
    explicit = _summary_value(article.summary, "Availability status")
    if explicit:
        return explicit
    haystack = f"{article.title} {article.summary}".lower()
    if any(term in haystack for term in ("매진", "sold out")):
        return "sold_out"
    if any(term in haystack for term in ("예매", "ticket open", "on sale")):
        return "on_sale"
    if "waitlist" in haystack:
        return "waitlist"
    return ""


def _signal_type(article: Article) -> str:
    haystack = f"{article.title} {article.summary}".lower()
    if any(term in haystack for term in ("sponsor", "후원")):
        return "sponsor"
    if any(term in haystack for term in ("exhibitor", "참가사")):
        return "exhibitor"
    if any(term in haystack for term in ("speaker", "연사")):
        return "speaker"
    return ""


def _event_occurrence_id(
    *,
    event_title: str,
    venue_id: str,
    event_date: str,
    city: str,
    online_flag: bool | None,
) -> str:
    if not event_title or not venue_id:
        return ""
    parts = [
        _slug(event_title),
        _slug(venue_id),
        _slug(event_date[:10] if event_date else ""),
        _slug(city),
        "online" if online_flag else "offline" if online_flag is False else "",
    ]
    parts = [part for part in parts if part]
    if len(parts) < 2:
        return ""
    return ":".join(parts)


def _required_field_gaps(row: Mapping[str, Any], event_model: str) -> list[str]:
    required_by_model = {
        "official_event_calendar": ["event_title", "venue_id", "source_url"],
        "ticket_availability": ["event_occurrence_id", "availability_status", "source_url"],
        "venue_calendar": ["venue_id", "event_occurrence_id", "source_url"],
        "exhibitor_sponsor_signal": [
            "event_occurrence_id",
            "organization_name",
            "signal_type",
        ],
    }
    gaps: list[str] = []
    for field_name in required_by_model.get(event_model, []):
        value = row.get(field_name)
        if value is None or value == "" or value == []:
            gaps.append(field_name)
    return gaps


def _first_non_empty(*values: object) -> str:
    for value in values:
        text = _string_value(value)
        if text:
            return text
    return ""


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower())
    slug = normalized.strip("-")
    if slug:
        return slug
    return f"u-{_digest(value)[:12]}" if value else ""


def _digest(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _as_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _age_days(generated_at: datetime, event_at: datetime) -> float:
    return max(0.0, (_as_utc(generated_at) - _as_utc(event_at)).total_seconds() / 86400)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _parse_datetime(value: str) -> datetime | None:
    if not value or value == "None":
        return None
    try:
        return _as_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None
