import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.core.database import engine, init_db
from app.core.logging import configure_logging

configure_logging()
init_db()

# ── Page configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Entropi Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium CSS Theme ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Base styles */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Main background */
.stApp {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #f1f5f9 100%);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    border-right: 1px solid rgba(148, 163, 184, 0.2);
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown label {
    color: #334155;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #ffffff, #f8fafc);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 16px;
    padding: 20px 24px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 20px rgba(148, 163, 184, 0.06), inset 0 1px 0 rgba(255,255,255,0.6);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(56, 189, 248, 0.15);
    border-color: rgba(56, 189, 248, 0.4);
}

div[data-testid="stMetric"] label {
    color: #64748b !important;
    font-weight: 500;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-weight: 700;
    font-size: 2rem;
}

/* Headers */
h1 {
    color: #0f172a !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}
h2, .stMarkdown h2 {
    color: #1e293b !important;
    font-weight: 700 !important;
    border-bottom: 2px solid rgba(56, 189, 248, 0.3);
    padding-bottom: 8px;
    margin-top: 2rem !important;
}
h3 {
    color: #334155 !important;
    font-weight: 600 !important;
}

/* Buttons */
.stButton > button {
    background: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    font-weight: 500;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.stButton > button:hover {
    background: #f8fafc;
    border-color: #38bdf8;
    color: #0284c7;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.12);
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(148, 163, 184, 0.2);
}

/* Divider */
hr {
    border-color: rgba(148, 163, 184, 0.2) !important;
}

/* Caption */
.stCaption, .stMarkdown small {
    color: #64748b !important;
}

/* Plotly chart containers */
div[data-testid="stPlotlyChart"] {
    border-radius: 16px;
    overflow: hidden;
}

/* Selectbox, multiselect */
div[data-testid="stSelectbox"],
div[data-testid="stMultiSelect"] {
    color: #0f172a;
}

/* Tabs */
button[data-baseweb="tab"] {
    color: #64748b !important;
    font-weight: 500;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #0284c7 !important;
    border-bottom-color: #0284c7 !important;
}

/* Remove default padding top */
.block-container {
    padding-top: 2rem;
}
</style>

""", unsafe_allow_html=True)

# ── Color palette ──────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#0284c7",       # Sky blue (darker for text contrast)
    "secondary": "#4f46e5",     # Indigo
    "accent": "#db2777",        # Pink
    "success": "#16a34a",       # Emerald
    "warning": "#d97706",       # Amber
    "danger": "#dc2626",        # Red
    "teal": "#0d9488",          # Teal
    "bg_card": "#ffffff",
    "bg_plot": "rgba(0,0,0,0)",
    "grid": "rgba(148, 163, 184, 0.12)",
    "text": "#1e293b",
    "text_muted": "#64748b",
}

CATEGORY_COLORS = {
    "Energy": "#d97706",
    "Environment": "#16a34a",
    "Infrastructure": "#0284c7",
    "Industry": "#4f46e5",
    "Academic": "#db2777",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["bg_plot"],
    plot_bgcolor=COLORS["bg_plot"],
    font=dict(family="Inter, sans-serif", color=COLORS["text"], size=13),
    dragmode=False,
)

_GRID_AXES = dict(
    xaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
)

_LEGEND_DEFAULT = dict(
    bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLORS["text_muted"], size=11),
)

PLOTLY_CONFIG = {"scrollZoom": False, "displayModeBar": False}


# ── Data loading from SQLite ───────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data(dataset_type: str) -> pd.DataFrame:
    """Load categorization results from the SQLite database."""
    query = """
        SELECT r.title AS "Title",
               r.year AS "Year",
               v.category AS "Category",
               v.status AS "Status",
               v.is_efficiency AS "Efficiency Focus",
               v.confidence_score AS "Category Score",
               v.gap AS "Category Gap",
               v.efficiency_score AS "Max Efficiency Score",
               v.alt_category AS "Alt Category",
               v.alt_score AS "Alt Score",
               v.reason AS "Reason"
        FROM researches r
        LEFT JOIN research_validation_flags v ON r.id = v.research_id
        WHERE r.contribution_category = :dataset_type
        ORDER BY r.year, r.title
    """
    df = pd.read_sql(query, engine, params={"dataset_type": dataset_type})
    df["Year"] = df["Year"].astype(str)
    return df


# ── Load entropy keyword reference from DB ──────────────────────────────────────
from app.services.keyword_store import load_efficiency_keyword_map


@st.cache_data(ttl=300)
def load_entropy_keywords():
    return load_efficiency_keyword_map(lang="EN")


entropy_keywords = load_entropy_keywords()


# ── Modal dialog for keywords ───────────────────────────────────────────────────
@st.dialog("Entropy Keywords", width="large")
def _show_keywords(category: str):
    st.subheader(category)
    for kw in entropy_keywords[category]:
        st.markdown(f"- {kw}")



# ── Title ───────────────────────────────x───────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 1rem 0 0.5rem 0;">
    <h1 style="
        font-size: 2.5rem;
        font-weight: 800;
        background: Black;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    ">Entropy Dashboard</h1>
    <p style="color: #64748b; font-size: 1rem; margin-top: 0.25rem;">
        Research Classification & Efficiency Analysis Dashboard
    </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <p style="
        font-weight: 700;
        font-size: 1.1rem;
        color: #0f172a;
        margin: 0.25rem 0 0 0;
    ">Entropy Deceleration</p>
    <p style="color: #64748b; font-size: 0.75rem; margin: 0;">v2.0 — SQLite Edition</p>
</div>
<hr style="border-color: rgba(148,163,184,0.15); margin: 0.5rem 0 1rem 0;">
""", unsafe_allow_html=True)

file_choice = st.sidebar.selectbox(
    "📂 Dataset",
    ["Research Projects", "Community Service"],
)
dataset_map = {
    "Research Projects": "research",
    "Community Service": "community_service",
}

df = load_data(dataset_map[file_choice])

if df.empty:
    st.warning("No data found in the database. Please run categorization first via the CLI.")
    st.code("python -m app.cli categorize --file data/reserach-project.xlsx --dataset_type research")
    st.stop()

# ── Year range filter ──────────────────────────────────────────────────────────
all_years = sorted(df["Year"].unique())
_default_start = all_years[-5] if len(all_years) >= 5 else all_years[0]
year_range = st.sidebar.select_slider(
    "📅 Year Range",
    options=all_years,
    value=(_default_start, all_years[-1]),
)
df_year = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
years = sorted(df_year["Year"].unique())

# ── Infographic Summary ────────────────────────────────────────────────────────
total = len(df_year)
yes_count = int((df_year["Efficiency Focus"] == "Yes").sum())
yes_pct = yes_count / total * 100 if total else 0
cat_count = df_year["Category"].nunique()
year_count = df_year["Year"].nunique()
# clear_count = int((df_year["Status"] == "Clear").sum())
# clear_pct = clear_count / total * 100 if total else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Records", f"{total:,}")
m2.metric("Entropy Related", f"{yes_count:,}")
m3.metric("% Entropy ", f"{yes_pct:.1f}%")
m4.metric("Years Covered", year_count)

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Efficiency Flag per Year
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Entropy Related Research per Year")

eff_year_data = (
    df_year.groupby(["Year", "Efficiency Focus"]).size()
    .reset_index(name="Count")
)

cols = st.columns(len(years))
for i, year in enumerate(years):
    yr_data = eff_year_data[eff_year_data["Year"] == year]
    y_count = int(yr_data[yr_data["Efficiency Focus"] == "Yes"]["Count"].sum())
    n_count = int(yr_data[yr_data["Efficiency Focus"] == "No"]["Count"].sum())
    yr_total = y_count + n_count
    pct = y_count / yr_total * 100 if yr_total else 0

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
    fig.update_layout(**_GRID_AXES)
    with cols[i]:
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

# ── Year drill-down buttons ───────────────────────────────────────────────────
btn_cols = st.columns(len(years))
st.session_state.setdefault("drill_year", None)

for i, year in enumerate(years):
    with btn_cols[i]:
        if st.button(f"{year}", key=f"btn_{year}", use_container_width=True):
            st.session_state["drill_year"] = year

# Drill-down detail section
if st.session_state["drill_year"]:
    drill_year = st.session_state["drill_year"]

    c1, c2 = st.columns([8, 1])
    with c1:
        st.markdown(f"### 📊 Detail for {drill_year}")
    with c2:
        if st.button("✕ Close", key="reset_drill", use_container_width=True):
            st.session_state["drill_year"] = None
            st.rerun()

    df_drill = df_year[df_year["Year"] == drill_year]

    # Category breakdown for this year
    cat_drill = (
        df_drill.groupby("Category")["Efficiency Focus"]
        .apply(lambda x: (x == "Yes").sum())
        .reset_index(name="Entropy Count")
    )
    cat_drill_total = df_drill.groupby("Category").size().reset_index(name="Total")
    cat_drill = cat_drill.merge(cat_drill_total, on="Category")

    DESIRED_ORDER = ["Energy", "Environment", "Industry", "Infrastructure","Information","Academic"]
    fig_drill = go.Figure()
    fig_drill.add_trace(go.Bar(
        x=cat_drill["Category"],
        y=cat_drill["Total"],
        name="Total",
        marker_color="rgba(148,163,184,0.2)",
        text=cat_drill["Total"],
        textposition="outside",
        textfont=dict(color=COLORS["text_muted"], size=11),
    ))
    fig_drill.add_trace(go.Bar(
        x=cat_drill["Category"],
        y=cat_drill["Entropy Count"],
        name="Entropy Related",
        marker_color=COLORS["teal"],
        text=cat_drill["Entropy Count"],
        textposition="outside",
        textfont=dict(color=COLORS["teal"], size=11),
    ))
    fig_drill.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text=f"Category Breakdown — {drill_year}",
            font=dict(size=16, color=COLORS["text"]),
        ),
        barmode="overlay",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(**_LEGEND_DEFAULT, orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        xaxis={**_GRID_AXES["xaxis"], "categoryorder": "array", "categoryarray": DESIRED_ORDER},
        yaxis=_GRID_AXES["yaxis"],
    )
    st.plotly_chart(fig_drill, width="stretch", config=PLOTLY_CONFIG)

    # Entropy keyword reference — modal per category
    st.caption("**Entropy Keywords by Category**")
    kw_btn_cols = st.columns(len(entropy_keywords))
    for j, cat in enumerate(entropy_keywords.keys()):
        with kw_btn_cols[j]:
            if st.button(cat, key=f"kw_cat_{cat}_{drill_year}", use_container_width=True):
                _show_keywords(cat)

    # Top efficiency Yes Researchs table
    st.markdown(f"#### Entropy Researches — {drill_year}")
    yes_drill = df_drill[df_drill["Efficiency Focus"] == "Yes"].sort_values(
        "Max Efficiency Score", ascending=False
    )
    st.dataframe(
        yes_drill[["Title", "Category", "Max Efficiency Score", "Reason"]].head(15),
        width="stretch",
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Category": st.column_config.TextColumn("Category", width="small"),
            "Max Efficiency Score": st.column_config.NumberColumn("Eff Score", format="%.4f"),
            "Reason": st.column_config.TextColumn("Reason", width="medium"),
        },
    )
    st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Trend line — Entropy Related count per year
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Entropy Research Trend")

eff_yes_only = eff_year_data[eff_year_data["Efficiency Focus"] == "Yes"].copy()
eff_no_only = eff_year_data[eff_year_data["Efficiency Focus"] == "No"].copy()

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
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
    fig_trend.add_trace(go.Scatter(
        x=eff_no_only["Year"],
        y=eff_no_only["Count"],
        mode="lines+markers",
        name="Non-Entropy ",
        line=dict(color=COLORS["text_muted"], width=2, dash="dot"),
        marker=dict(size=7, color=COLORS["text_muted"]),
    ))

max_y = max(eff_yes_only["Count"].max(), eff_no_only["Count"].max() if not eff_no_only.empty else 0)
fig_trend.update_layout(
    **PLOTLY_LAYOUT,
    title=dict(
        text="Trend of Entropy Projects Over Time",
        font=dict(size=16, color=COLORS["text"]),
    ),
    height=420,
    margin=dict(l=40, r=40, t=60, b=40),
    yaxis=dict(
        range=[0, max_y * 1.3],
        gridcolor=COLORS["grid"],
        zerolinecolor=COLORS["grid"],
    ),
    xaxis=dict(
        dtick=1,
        tickformat="d",
        gridcolor=COLORS["grid"],
        zerolinecolor=COLORS["grid"],
    ),
    legend=dict(**_LEGEND_DEFAULT, orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
)
st.plotly_chart(fig_trend, width="stretch", config=PLOTLY_CONFIG)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Category Distribution
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Category Distribution")

dist_col1, dist_col2 = st.columns([2, 3])

with dist_col1:
    cat_counts = df_year["Category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    cat_colors = [CATEGORY_COLORS.get(c, COLORS["text_muted"]) for c in cat_counts["Category"]]

    fig_donut = go.Figure(data=[go.Pie(
        labels=cat_counts["Category"],
        values=cat_counts["Count"],
        hole=0.55,
        marker_colors=cat_colors,
        textinfo="label+percent",
        textfont=dict(size=12, color="#fff"),
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        sort=False,
    )])
    fig_donut.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text="Overall Category Split",
            font=dict(size=14, color=COLORS["text"]),
        ),
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
    st.plotly_chart(fig_donut, width="stretch", config=PLOTLY_CONFIG)

with dist_col2:
    # Status breakdown per category
    status_cat = (
        df_year.groupby(["Category", "Status"]).size()
        .reset_index(name="Count")
    )
    status_colors = {
        "Clear": COLORS["success"],
        "Ambiguous": COLORS["warning"],
        "Uncategorized": COLORS["danger"],
    }

    fig_status = go.Figure()
    for status in ["Clear", "Ambiguous", "Uncategorized"]:
        s_data = status_cat[status_cat["Status"] == status]
        fig_status.add_trace(go.Bar(
            x=s_data["Category"],
            y=s_data["Count"],
            name=status,
            marker_color=status_colors.get(status, COLORS["text_muted"]),
            text=s_data["Count"],
            textposition="outside",
            textfont=dict(size=10),
        ))

    fig_status.update_layout(
        **PLOTLY_LAYOUT,
        **_GRID_AXES,
        title=dict(
            text="Classification Confidence by Category",
            font=dict(size=14, color=COLORS["text"]),
        ),
        barmode="stack",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(**_LEGEND_DEFAULT, orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_status, width="stretch", config=PLOTLY_CONFIG)




# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Model Confidence Distribution
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Model Confidence Distribution")

from app.core.config import settings as _settings

conf_col1, conf_col2 = st.columns([3, 2])

with conf_col1:
    fig_hist = go.Figure(data=[go.Histogram(
        x=df_year["Category Score"],
        nbinsx=25,
        marker_color=COLORS["primary"],
        opacity=0.85,
        hovertemplate="Score: %{x:.2f}<br>Count: %{y}<extra></extra>",
    )])
    fig_hist.add_vline(
        x=_settings.CONFIDENCE_THRESHOLD,
        line_dash="dash",
        line_color=COLORS["danger"],
        line_width=2,
        annotation_text=f"Threshold ({_settings.CONFIDENCE_THRESHOLD})",
        annotation_position="top right",
        annotation_font_color=COLORS["danger"],
    )
    fig_hist.update_layout(
        **PLOTLY_LAYOUT,
        **_GRID_AXES,
        title=dict(
            text="Category Score Distribution",
            font=dict(size=14, color=COLORS["text"]),
        ),
        xaxis_title="Confidence Score",
        yaxis_title="Count",
        height=380,
        margin=dict(l=40, r=40, t=60, b=40),
        bargap=0.05,
    )
    st.plotly_chart(fig_hist, width="stretch", config=PLOTLY_CONFIG)

with conf_col2:
    low_conf = int((df_year["Category Score"] < _settings.CONFIDENCE_THRESHOLD).sum())
    ambiguous = int((df_year["Status"] == "Ambiguous").sum())
    uncategorized = int((df_year["Status"] == "Uncategorized").sum())
    clear = int((df_year["Status"] == "Clear").sum())
    conf_total = len(df_year)

    st.markdown("### Classification Quality")
    st.metric("Clear", f"{clear:,}", f"{clear/conf_total*100:.1f}%" if conf_total else "0%")
    st.metric("Ambiguous", f"{ambiguous:,}", f"{ambiguous/conf_total*100:.1f}%" if conf_total else "0%",
              delta_color="inverse")
    st.metric("Uncategorized", f"{uncategorized:,}", f"{uncategorized/conf_total*100:.1f}%" if conf_total else "0%",
              delta_color="inverse")
    st.caption(f"Confidence threshold: **{_settings.CONFIDENCE_THRESHOLD}** · Gap threshold: **{_settings.GAP_THRESHOLD}**")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: Author Analytics
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Author Analytics")


@st.cache_data(ttl=300)
def load_author_stats(dataset_type: str) -> pd.DataFrame:
    """Top authors by total research output and entropy contribution."""
    query = """
        SELECT
            a.name        AS "Author",
            a.nidn        AS "NIDN",
            COUNT(r.id)   AS "Total",
            SUM(CASE WHEN v.is_efficiency = 'Yes' THEN 1 ELSE 0 END) AS "Entropy"
        FROM authors a
        JOIN research_authors ra ON a.id = ra.author_id
        JOIN researches r        ON ra.research_id = r.id
        LEFT JOIN research_validation_flags v ON r.id = v.research_id
        WHERE r.contribution_category = :dataset_type
        GROUP BY a.id
        ORDER BY "Total" DESC
    """
    df_auth = pd.read_sql(query, engine, params={"dataset_type": dataset_type})
    df_auth["% Entropy"] = (df_auth["Entropy"] / df_auth["Total"] * 100).round(1)
    return df_auth


author_df = load_author_stats(dataset_map[file_choice])

if author_df.empty:
    st.info("No author data available for this dataset.")
else:
    auth_search = st.text_input("🔍 Search authors...", placeholder="Type a name or NIDN", key="author_search")
    display_authors = author_df.copy()
    if auth_search:
        mask = (
            display_authors["Author"].str.contains(auth_search, case=False, na=False)
            | display_authors["NIDN"].astype(str).str.contains(auth_search, case=False, na=False)
        )
        display_authors = display_authors[mask]

    st.dataframe(
        display_authors,
        width="stretch",
        hide_index=True,
        column_config={
            "Author": st.column_config.TextColumn("Author", width="large"),
            "NIDN": st.column_config.TextColumn("NIDN", width="medium"),
            "Total": st.column_config.NumberColumn("Total", format="%d"),
            "Entropy": st.column_config.NumberColumn("Entropy", format="%d"),
            "% Entropy": st.column_config.NumberColumn("% Entropy", format="%.1f%%"),
        },
    )
    st.caption(f"{len(display_authors):,} authors shown")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: Raw Data Explorer
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Raw Data Explorer")

with st.expander("📋 View Full Dataset", expanded=False):
    search_term = st.text_input("🔍 Search titles...", placeholder="Type to filter by title", key="raw_search")
    display_df = df_year.copy()
    if search_term:
        display_df = display_df[display_df["Title"].str.contains(search_term, case=False, na=False)]

    st.caption(f"{len(display_df):,} records")
    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Year": st.column_config.TextColumn("Year", width="small"),
            "Category": st.column_config.TextColumn("Category", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Efficiency Focus": st.column_config.TextColumn("Entropy", width="small"),
            "Category Score": st.column_config.NumberColumn("Score", format="%.4f"),
            "Category Gap": st.column_config.NumberColumn("Gap", format="%.4f"),
            "Max Efficiency Score": st.column_config.NumberColumn("Eff Score", format="%.4f"),
            "Alt Category": st.column_config.TextColumn("Alt Cat", width="small"),
            "Alt Score": st.column_config.NumberColumn("Alt Score", format="%.4f"),
            "Reason": st.column_config.TextColumn("Reason", width="medium"),
        },
    )


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 2rem 0 1rem 0; color: #64748b; font-size: 0.8rem;">
    <hr style="border-color: rgba(148, 163, 184, 0.15); margin-bottom: 1rem;">
    Built with Streamlit &amp; Plotly &nbsp;·&nbsp; Data powered by SQLite &nbsp;·&nbsp; Model: all-MiniLM-L6-v2
</div>
""", unsafe_allow_html=True)

