from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from html import escape
from pathlib import Path
from typing import Any, Mapping

from radar_core.ontology import build_summary_ontology_metadata
from radar_core.report_utils import (
    generate_index_html as _core_generate_index_html,
)
from radar_core.report_utils import (
    generate_report as _core_generate_report,
)

from .models import Article, CategoryConfig


def generate_report(
    *,
    category: CategoryConfig,
    articles: Iterable[Article],
    output_path: Path,
    stats: dict[str, int],
    errors: list[str] | None = None,
    store=None,
    quality_report: Mapping[str, Any] | None = None,
) -> Path:
    """Generate HTML report (delegates to radar-core)."""
    articles_list = [_sanitize_article_for_report(article) for article in articles]
    plugin_charts = []

    # --- Universal plugins (entity heatmap + source reliability) ---
    try:
        from radar_core.plugins.entity_heatmap import get_chart_config as _heatmap_config

        _heatmap = _heatmap_config(articles=articles_list)
        if _heatmap is not None:
            plugin_charts.append(_heatmap)
    except Exception:
        pass
    try:
        from radar_core.plugins.source_reliability import get_chart_config as _reliability_config

        _reliability = _reliability_config(store=store)
        if _reliability is not None:
            plugin_charts.append(_reliability)
    except Exception:
        pass

    result = _core_generate_report(
        category=category,
        articles=articles_list,
        output_path=output_path,
        stats=stats,
        errors=errors,
        plugin_charts=plugin_charts if plugin_charts else None,
        ontology_metadata=build_summary_ontology_metadata(
            "EventRadar",
            category_name=category.category_name,
            search_from=Path(__file__).resolve(),
        ),
    )
    if quality_report:
        _inject_event_quality_panel(result, category.category_name, quality_report)
    return result


def generate_index_html(
    report_dir: Path,
    summaries_dir: Path | None = None,
) -> Path:
    """Generate index.html (delegates to radar-core)."""
    radar_name = "Event Radar"
    return _core_generate_index_html(report_dir, radar_name)


def _inject_event_quality_panel(
    output_path: Path,
    category_name: str,
    quality_report: Mapping[str, Any],
) -> None:
    _inject_event_quality_panel_into(output_path, quality_report)
    dated_reports = sorted(
        output_path.parent.glob(
            f"{category_name}_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].html"
        ),
        key=lambda path: path.stat().st_mtime,
    )
    if dated_reports:
        _inject_event_quality_panel_into(dated_reports[-1], quality_report)


def _inject_event_quality_panel_into(
    output_path: Path,
    quality_report: Mapping[str, Any],
) -> None:
    if not output_path.exists():
        return
    html = output_path.read_text(encoding="utf-8")
    if 'id="event-quality"' in html:
        return
    marker = '<section id="entities"'
    if marker not in html:
        return
    panel = _render_event_quality_panel(quality_report).rstrip()
    rendered = html.replace(marker, panel + "\n      " + marker, 1)
    rendered = "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"
    output_path.write_text(rendered, encoding="utf-8")


def _render_event_quality_panel(quality_report: Mapping[str, Any]) -> str:
    summary = quality_report.get("summary")
    summary_map = summary if isinstance(summary, Mapping) else {}
    sources = [row for row in _list(quality_report.get("sources")) if isinstance(row, Mapping)]
    events = [row for row in _list(quality_report.get("events")) if isinstance(row, Mapping)]
    review_items = [
        row for row in _list(quality_report.get("daily_review_items")) if isinstance(row, Mapping)
    ]
    flagged_sources = [
        row
        for row in sources
        if str(row.get("status")) in {"missing", "missing_event", "stale", "unknown_event_date"}
    ][:8]
    chips = [
        ("official", summary_map.get("official_event_calendar_events", 0)),
        ("tickets", summary_map.get("ticket_availability_events", 0)),
        ("venue", summary_map.get("venue_calendar_events", 0)),
        ("exhibitor", summary_map.get("exhibitor_sponsor_signal_events", 0)),
        ("occurrences", summary_map.get("event_occurrence_present_count", 0)),
        ("field gaps", summary_map.get("event_required_field_gap_count", 0)),
        ("fresh", summary_map.get("fresh_sources", 0)),
        ("missing", summary_map.get("missing_sources", 0)),
        ("review", summary_map.get("daily_review_item_count", 0)),
    ]
    chip_html = "\n".join(
        f'<span class="chip"><strong>{escape(label)}</strong> {escape(str(value))}</span>'
        for label, value in chips
    )
    return f"""
      <section id="event-quality" class="section" aria-label="Event quality">
        <div class="section-hd">
          <h2>Event Quality</h2>
          <div class="right">
            <span class="kbd">event_quality.json</span>
            <span class="kbd">calendar + ticket evidence</span>
          </div>
        </div>
        <article class="panel">
          <header class="panel-hd">
            <div>
              <p class="panel-title">Event Source Coverage</p>
              <p class="panel-sub">official calendars, ticket availability, venue calendars, exhibitor and sponsor signals</p>
            </div>
          </header>
          <div class="panel-bd">
            <div class="row" aria-label="Event quality summary">
              {chip_html}
            </div>
            {_render_event_quality_sources(flagged_sources)}
            {_render_event_quality_events(events[:8])}
            {_render_event_quality_review(review_items[:8])}
          </div>
        </article>
      </section>
"""


def _render_event_quality_sources(sources: list[Mapping[str, Any]]) -> str:
    if not sources:
        return '<p class="muted small">No stale or missing tracked event sources in this run.</p>'
    items: list[str] = []
    for row in sources:
        source = escape(str(row.get("source", "")))
        status = escape(str(row.get("status", "")))
        model = escape(str(row.get("event_model", "")))
        age = row.get("age_days")
        age_text = "" if age is None else f", age {escape(str(age))}d"
        items.append(f"<li><strong>{source}</strong>: {status} ({model}{age_text})</li>")
    return "<ul>" + "\n".join(items) + "</ul>"


def _render_event_quality_events(events: list[Mapping[str, Any]]) -> str:
    if not events:
        return '<p class="muted small">No tracked event-quality rows in this run.</p>'
    items: list[str] = []
    for row in events:
        model = escape(str(row.get("event_model", "")))
        source = escape(str(row.get("source", "")))
        title = escape(_normalize_report_text(str(row.get("title", "")))[:120])
        occurrence = escape(str(row.get("event_occurrence_id", "")))
        suffix = "" if not occurrence else f" ({occurrence})"
        items.append(f"<li><strong>{model}</strong> {source}: {title}{suffix}</li>")
    return "<ul>" + "\n".join(items) + "</ul>"


def _render_event_quality_review(items: list[Mapping[str, Any]]) -> str:
    if not items:
        return '<p class="muted small">No event review items in this run.</p>'
    rendered: list[str] = []
    for row in items:
        reason = escape(str(row.get("reason", "")))
        model = escape(str(row.get("event_model", "")))
        source = escape(str(row.get("source", "")))
        gaps = row.get("required_field_gaps")
        if isinstance(gaps, list) and gaps:
            detail = ", ".join(escape(str(gap)) for gap in gaps)
        else:
            detail = escape(
                _normalize_report_text(
                    str(row.get("status") or row.get("detail") or row.get("title") or "")
                )
            )
        rendered.append(f"<li><strong>{reason}</strong> {model} {source}: {detail}</li>")
    return "<ul>" + "\n".join(rendered) + "</ul>"


def _sanitize_article_for_report(article: Article) -> Article:
    title = _normalize_report_text(article.title)
    summary = _normalize_report_text(article.summary)
    if title == article.title and summary == article.summary:
        return article
    return replace(article, title=title, summary=summary)


def _normalize_report_text(value: str) -> str:
    return " ".join(value.split())


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
