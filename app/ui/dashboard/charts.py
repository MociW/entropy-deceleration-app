"""
Dashboard chart builders — pure functions, no Streamlit calls.

Every function in this module accepts data and returns a ``plotly.graph_objects.Figure``.
No ``st.*`` calls are made here, which keeps charts independently testable
and makes it easy to reuse them on other pages.
"""
import pandas as pd
import plotly.graph_objects as go

from app.ui.dashboard.theme import (
    COLORS,
    CATEGORY_COLORS,
    CATEGORY_ORDER,
    PLOTLY_LAYOUT,
    GRID_AXES,
    LEGEND_DEFAULT,
)

# ── Section 1: Entropy per Year ────────────────────────────────────────────────

def make_entropy_pie(year: str, y_count: int, n_count: int, pct: float) -> go.Figure:
    """Donut chart showing the entropy vs non-entropy ratio for a single year.

    Args:
        year:    Year label string.
        y_count: Number of entropy-related records.
        n_count: Number of non-entropy records.
        pct:     Percentage of entropy-related records (0–100).

    Returns:
        Plotly Figure.
    """
    yr_total = y_count + n_count
    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Entropy ", "Non-Entropy "],
                values=[y_count, n_count],
                hole=0.6,
                marker_colors=[COLORS["teal"], "#e2e8f0"],
                textinfo="none",
                hoverinfo="label+value+percent",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text=f"<b style='font-size:28px;color:{COLORS['text']}'>{year}</b><br>"
                 f"<span style='font-size:18px;color:{COLORS['text_muted']}'>"
                 f"{pct:.1f}% ({y_count}/{yr_total})</span>",
            font=dict(size=20),
        ),
        height=360,
        margin=dict(l=10, r=10, t=70, b=10),
        showlegend=False,
        annotations=[
            dict(
                text=f"<b>{pct:.0f}%</b>",
                x=0.5, y=0.5,
                font_size=28,
                font_color=COLORS["teal"],
                showarrow=False,
            )
        ],
    )
    fig.update_layout(**GRID_AXES)
    return fig


# ── Section 1: Year drill-down ─────────────────────────────────────────────────

def make_drill_chart(cat_drill: pd.DataFrame, drill_year: str) -> go.Figure:
    """Overlay bar chart: total vs entropy count per category for a given year.

    Args:
        cat_drill:  DataFrame with columns Category, Entropy Count, Total.
        drill_year: Year label string used in the chart title.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cat_drill["Category"],
        y=cat_drill["Total"],
        name="Total",
        marker_color="rgba(148,163,184,0.2)",
        text=cat_drill["Total"],
        textposition="outside",
        textfont=dict(color=COLORS["text_muted"], size=11),
    ))
    fig.add_trace(go.Bar(
        x=cat_drill["Category"],
        y=cat_drill["Entropy Count"],
        name="Entropy Related",
        marker_color=COLORS["teal"],
        text=cat_drill["Entropy Count"],
        textposition="outside",
        textfont=dict(color=COLORS["teal"], size=11),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text=f"Category Breakdown — {drill_year}",
            font=dict(size=16, color=COLORS["text"]),
        ),
        barmode="overlay",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(**LEGEND_DEFAULT, orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        xaxis={**GRID_AXES["xaxis"], "categoryorder": "array", "categoryarray": CATEGORY_ORDER},
        yaxis=GRID_AXES["yaxis"],
    )
    return fig


# ── Section 2: Trend line ──────────────────────────────────────────────────────

def make_trend_chart(eff_yes_only: pd.DataFrame, eff_no_only: pd.DataFrame) -> go.Figure:
    """Line chart showing the entropy research trend over years.

    Args:
        eff_yes_only: Filtered DataFrame for Efficiency Focus == "Yes".
        eff_no_only:  Filtered DataFrame for Efficiency Focus == "No".

    Returns:
        Plotly Figure.
    """
    max_y = max(
        eff_yes_only["Count"].max() if not eff_yes_only.empty else 0,
        eff_no_only["Count"].max() if not eff_no_only.empty else 0,
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=eff_yes_only["Year"],
        y=eff_yes_only["Count"],
        mode="lines+markers+text",
        name="Entropy Related",
        line=dict(color=COLORS["teal"], width=3),
        marker=dict(size=10, color=COLORS["teal"], line=dict(width=2, color="#ffffff")),
        text=eff_yes_only["Count"],
        textposition="top center",
        textfont=dict(color=COLORS["teal"], size=12, weight="bold"),
        fill="tozeroy",
        fillcolor="rgba(13,148,136,0.06)",
    ))
    if not eff_no_only.empty:
        fig.add_trace(go.Scatter(
            x=eff_no_only["Year"],
            y=eff_no_only["Count"],
            mode="lines+markers",
            name="Non-Entropy ",
            line=dict(color=COLORS["text_muted"], width=2, dash="dot"),
            marker=dict(size=7, color=COLORS["text_muted"]),
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text="Trend of Entropy Projects Over Time",
            font=dict(size=16, color=COLORS["text"]),
        ),
        height=420,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(range=[0, max_y * 1.3], gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
        xaxis=dict(dtick=1, tickformat="d", gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
        legend=dict(**LEGEND_DEFAULT, orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    return fig


# ── Section 3: Category distribution ──────────────────────────────────────────

def make_category_donut(cat_counts: pd.DataFrame, total: int) -> go.Figure:
    """Donut chart showing the overall split of records across categories.

    Args:
        cat_counts: DataFrame with columns Category and Count.
        total:      Total number of records (shown in center annotation).

    Returns:
        Plotly Figure.
    """
    cat_colors = [CATEGORY_COLORS.get(c, COLORS["text_muted"]) for c in cat_counts["Category"]]
    fig = go.Figure(data=[go.Pie(
        labels=cat_counts["Category"],
        values=cat_counts["Count"],
        hole=0.55,
        marker_colors=cat_colors,
        textinfo="label+percent",
        textfont=dict(size=12, color="#fff"),
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        sort=False,
    )])
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Overall Category Split", font=dict(size=14, color=COLORS["text"])),
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=False,
        annotations=[
            dict(
                text=f"<b>{total:,}</b><br><span style='font-size:11px'>total</span>",
                x=0.5, y=0.5,
                font_size=22,
                font_color=COLORS["text"],
                showarrow=False,
            )
        ],
    )
    return fig


def make_status_bar(status_cat: pd.DataFrame) -> go.Figure:
    """Stacked bar chart showing classification status breakdown per category.

    Args:
        status_cat: DataFrame with columns Category, Status, Count.

    Returns:
        Plotly Figure.
    """
    status_colors = {
        "Clear": COLORS["success"],
        "Ambiguous": COLORS["warning"],
        "Uncategorized": COLORS["danger"],
    }
    fig = go.Figure()
    for status in ["Clear", "Ambiguous", "Uncategorized"]:
        s_data = status_cat[status_cat["Status"] == status]
        fig.add_trace(go.Bar(
            x=s_data["Category"],
            y=s_data["Count"],
            name=status,
            marker_color=status_colors.get(status, COLORS["text_muted"]),
            text=s_data["Count"],
            textposition="outside",
            textfont=dict(size=10),
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        **GRID_AXES,
        title=dict(
            text="Classification Confidence by Category",
            font=dict(size=14, color=COLORS["text"]),
        ),
        barmode="stack",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(**LEGEND_DEFAULT, orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    return fig


# ── Section 5: Model confidence ────────────────────────────────────────────────

def make_confidence_histogram(df_year: pd.DataFrame, conf_threshold: float) -> go.Figure:
    """Histogram of category confidence scores with a threshold reference line.

    Args:
        df_year:          Filtered DataFrame for the selected year range.
        conf_threshold:   The confidence threshold value to draw as a vertical line.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure(data=[go.Histogram(
        x=df_year["Category Score"],
        nbinsx=25,
        marker_color=COLORS["primary"],
        opacity=0.85,
        hovertemplate="Score: %{x:.2f}<br>Count: %{y}<extra></extra>",
    )])
    fig.add_vline(
        x=conf_threshold,
        line_dash="dash",
        line_color=COLORS["danger"],
        line_width=2,
        annotation_text=f"Threshold ({conf_threshold})",
        annotation_position="top right",
        annotation_font_color=COLORS["danger"],
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        **GRID_AXES,
        title=dict(text="Category Score Distribution", font=dict(size=14, color=COLORS["text"])),
        xaxis_title="Confidence Score",
        yaxis_title="Count",
        height=380,
        margin=dict(l=40, r=40, t=60, b=40),
        bargap=0.05,
    )
    return fig
