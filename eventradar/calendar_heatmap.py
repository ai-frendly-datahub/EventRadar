"""Calendar heatmap generator for event distribution visualization.

Generates GitHub contribution-style calendar heatmap showing event dates
across weeks and days of week for the last 90 days.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import plotly.graph_objects as go


if TYPE_CHECKING:
    from collections.abc import Iterable

    from .models import Article


def build_calendar_heatmap(
    articles: Iterable[Article],
    days_back: int = 90,
) -> str:
    """Build calendar heatmap HTML from articles.

    Args:
        articles: Iterable of Article objects with published dates
        days_back: Number of days to include (default 90)

    Returns:
        HTML string (full_html=False, include_plotlyjs='cdn')
    """
    articles_list = list(articles)

    # Calculate date range
    now = datetime.now(UTC)
    start_date = now - timedelta(days=days_back)

    # Build week x day matrix
    # Key: (week_number, day_of_week), Value: count
    date_counts: dict[tuple[int, int], int] = defaultdict(int)

    for article in articles_list:
        if not article.published:
            continue

        pub_date = article.published
        # Ensure timezone-aware comparison
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=UTC)

        if pub_date < start_date:
            continue

        # Get ISO calendar (year, week, weekday)
        iso_cal = pub_date.isocalendar()
        week_num = iso_cal[1]  # 1-53
        day_of_week = iso_cal[2]  # 1=Mon, 7=Sun

        date_counts[(week_num, day_of_week)] += 1

    # Build matrix: 53 weeks x 7 days
    weeks = list(range(1, 54))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Initialize matrix (7 rows x 53 columns)
    z_matrix = [[0 for _ in range(53)] for _ in range(7)]

    for (week_num, day_of_week), count in date_counts.items():
        if 1 <= week_num <= 53 and 1 <= day_of_week <= 7:
            # day_of_week is 1-7, convert to 0-6 for matrix indexing
            z_matrix[day_of_week - 1][week_num - 1] = count

    # Create Plotly heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=z_matrix,
            x=weeks,
            y=days,
            colorscale="YlGn",
            hovertemplate="Week %{x}<br>%{y}<br>Events: %{z}<extra></extra>",
            colorbar=dict(
                title="Event<br>Count",
                thickness=15,
                len=0.7,
            ),
        )
    )

    fig.update_layout(
        title="Event Distribution Calendar (Last 90 Days)",
        xaxis_title="Week of Year",
        yaxis_title="Day of Week",
        width=1000,
        height=300,
        margin=dict(l=80, r=80, t=60, b=60),
        plot_bgcolor="rgba(240, 240, 240, 0.5)",
        paper_bgcolor="rgba(255, 255, 255, 0.95)",
        font=dict(family="system-ui, sans-serif", size=12),
        xaxis=dict(
            tickmode="linear",
            tick0=1,
            dtick=4,
        ),
    )

    # Return HTML without full document structure (for embedding)
    html: str = fig.to_html(full_html=False, include_plotlyjs="cdn")
    return html
