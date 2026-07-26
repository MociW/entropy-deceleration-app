"""
Entropy Dashboard — Streamlit entry point.

Run with:
    streamlit run app/ui/dashboard/main.py

or via the Makefile:
    make run

This module is responsible only for page layout and Streamlit state management.
All data loading is delegated to ``data.py``,
all chart construction to ``charts.py``,
and all visual constants to ``theme.py``.
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path when launched via `streamlit run`.
# This is required because Streamlit adds the script's directory, not the CWD.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import datetime

import streamlit as st

from app.core.database import init_db
from app.core.logger import configure_logging
from app.ui.dashboard.charts import (
    make_category_donut,
    make_confidence_histogram,
    make_drill_chart,
    make_entropy_pie,
    make_status_bar,
    make_trend_chart,
)
from app.ui.dashboard.data import load_active_thresholds, load_data, load_entropy_keywords
from app.ui.dashboard.theme import PLOTLY_CONFIG, inject_css

# ── Bootstrap ──────────────────────────────────────────────────────────────────
configure_logging()
init_db()

# ── Page configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Entropi Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Entropy keyword reference (loaded once per session) ────────────────────────
entropy_keywords = load_entropy_keywords()


# ── Modal dialog for keywords ───────────────────────────────────────────────────
@st.dialog("Entropy Keywords", width="large")
def _show_keywords(category: str) -> None:
    st.subheader(category)
    for kw in entropy_keywords[category]:
        st.markdown(f"- {kw}")


# ── Title ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 1rem 0 0.5rem 0;">
    <h1 style="
        font-size: 3rem;
        font-weight: 800;
        background: Black;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    ">Entropy Dashboard</h1>
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
    st.warning("No data found in the database. Please import and categorize data first via the API endpoints.")
    st.code("curl -X POST http://localhost:8000/api/v1/pipeline/import -H 'X-API-Key: YOUR_KEY' -F 'file=@data/reserach-project.xlsx'")
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

# ── Infographic summary metrics ────────────────────────────────────────────────
total = len(df_year)
yes_count = int((df_year["Efficiency Focus"] == "Yes").sum())
yes_pct = yes_count / total * 100 if total else 0
year_count = df_year["Year"].nunique()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Records", f"{total:,}")
m2.metric("Entropy Related", f"{yes_count:,}")
m3.metric("% Entropy ", f"{yes_pct:.1f}%")
m4.metric("Years Covered", year_count)

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Entropy flag per year
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

    with cols[i]:
        st.plotly_chart(make_entropy_pie(year, y_count, n_count, pct), width="stretch", config=PLOTLY_CONFIG)

# ── Year drill-down buttons ────────────────────────────────────────────────────
btn_cols = st.columns(len(years))
st.session_state.setdefault("drill_year", None)

for i, year in enumerate(years):
    with btn_cols[i]:
        if st.button(f"{year}", key=f"btn_{year}", width="stretch"):
            st.session_state["drill_year"] = year

# Drill-down detail section
if st.session_state["drill_year"]:
    drill_year = st.session_state["drill_year"]

    c1, c2 = st.columns([8, 1])
    with c1:
        st.markdown(f"### 📊 Detail for {drill_year}")
    with c2:
        if st.button("✕ Close", key="reset_drill", width="stretch"):
            st.session_state["drill_year"] = None
            st.rerun()

    df_drill = df_year[df_year["Year"] == drill_year]

    cat_drill = (
        df_drill.groupby("Category")["Efficiency Focus"]
        .apply(lambda x: (x == "Yes").sum())
        .reset_index(name="Entropy Count")
    )
    cat_drill_total = df_drill.groupby("Category").size().reset_index(name="Total")
    cat_drill = cat_drill.merge(cat_drill_total, on="Category")

    st.plotly_chart(make_drill_chart(cat_drill, drill_year), width="stretch", config=PLOTLY_CONFIG)

    # Entropy keyword reference — modal per category
    st.caption("**Entropy Keywords by Category**")
    kw_btn_cols = st.columns(len(entropy_keywords))
    for j, cat in enumerate(entropy_keywords.keys()):
        with kw_btn_cols[j]:
            if st.button(cat, key=f"kw_cat_{cat}_{drill_year}", width="stretch"):
                _show_keywords(cat)

    # Top entropy research table
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
# SECTION 2: Entropy trend line
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Entropy Research Trend")

eff_yes_only = eff_year_data[eff_year_data["Efficiency Focus"] == "Yes"].copy()
eff_no_only = eff_year_data[eff_year_data["Efficiency Focus"] == "No"].copy()

st.plotly_chart(make_trend_chart(eff_yes_only, eff_no_only), width="stretch", config=PLOTLY_CONFIG)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Category distribution
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Category Distribution")

dist_col1, dist_col2 = st.columns([2, 3])

with dist_col1:
    cat_counts = df_year["Category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    st.plotly_chart(make_category_donut(cat_counts, total), width="stretch", config=PLOTLY_CONFIG)

with dist_col2:
    status_cat = (
        df_year.groupby(["Category", "Status"]).size()
        .reset_index(name="Count")
    )
    st.plotly_chart(make_status_bar(status_cat), width="stretch", config=PLOTLY_CONFIG)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Model confidence distribution
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Model Confidence Distribution")

_thresholds = load_active_thresholds()
_conf_threshold = _thresholds["confidence_threshold"]
_gap_threshold = _thresholds["gap_threshold"]

conf_col1, conf_col2 = st.columns([3, 2])

with conf_col1:
    st.plotly_chart(
        make_confidence_histogram(df_year, _conf_threshold),
        width="stretch",
        config=PLOTLY_CONFIG,
    )

with conf_col2:
    low_conf = int((df_year["Category Score"] < _conf_threshold).sum())
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
    st.caption(f"Confidence threshold: **{_conf_threshold}** · Gap threshold: **{_gap_threshold}**")


# ── Footer ─────────────────────────────────────────────────────────────────────
current_year = datetime.datetime.now().year
st.markdown(f"""
<div style="text-align: center; padding: 2rem 0 1rem 0; color: #64748b; font-size: 0.8rem;">
    <hr style="border-color: rgba(148, 163, 184, 0.15); margin-bottom: 1rem;">
    {current_year} © Pusat Kajian Perlambatan Entropi
</div>
""", unsafe_allow_html=True)
