"""
Dashboard visual design system — CSS theme, color palette, and Plotly defaults.

This module is pure Python constants with zero runtime side effects.
Import and call ``inject_css()`` once at app startup to apply the theme.
"""
import streamlit as st

# ── Color palette ──────────────────────────────────────────────────────────────

COLORS: dict[str, str] = {
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

CATEGORY_COLORS: dict[str, str] = {
    "Energy": "#d97706",
    "Environment": "#16a34a",
    "Infrastructure": "#0284c7",
    "Industry": "#4f46e5",
    "Academic": "#db2777",
}

# ── Plotly shared layout defaults ──────────────────────────────────────────────

PLOTLY_LAYOUT: dict = dict(
    paper_bgcolor=COLORS["bg_plot"],
    plot_bgcolor=COLORS["bg_plot"],
    font=dict(family="Inter, sans-serif", color=COLORS["text"], size=13),
    dragmode=False,
)

GRID_AXES: dict = dict(
    xaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
)

LEGEND_DEFAULT: dict = dict(
    bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLORS["text_muted"], size=11),
)

PLOTLY_CONFIG: dict = {"scrollZoom": False, "displayModeBar": False}

# Category display order used across multiple charts
CATEGORY_ORDER: list[str] = ["Energy", "Environment", "Industry", "Infrastructure", "Information", "Academic"]

# ── CSS injection ──────────────────────────────────────────────────────────────

_CSS = """
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
"""


def inject_css() -> None:
    """Inject the dashboard CSS theme into the Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)
