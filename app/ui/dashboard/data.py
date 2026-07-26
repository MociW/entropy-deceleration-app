"""
Dashboard cached data loaders.

All functions here are decorated with ``@st.cache_data`` and act as the
boundary between the UI layer and the service/database layer.
No layout, chart, or CSS code lives in this module.
"""
import pandas as pd
import streamlit as st

from app.core.database import engine
from app.util.keyword_store import load_efficiency_keyword_map
from app.util.keyword_store import load_thresholds as _load_thresholds


@st.cache_data(ttl=300)
def load_data(dataset_type: str) -> pd.DataFrame:
    """Load categorization results from the SQLite database.

    Args:
        dataset_type: One of ``"research"`` or ``"community_service"``.

    Returns:
        DataFrame with columns: Title, Year, Category, Status, Efficiency Focus,
        Category Score, Category Gap, Max Efficiency Score, Alt Category, Alt Score, Reason.
    """
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


@st.cache_data(ttl=300)
def load_entropy_keywords() -> dict[str, list[str]]:
    """Load the EN entropy keyword map from the database.

    Returns:
        Dict mapping category label → list of keywords.
    """
    return load_efficiency_keyword_map(lang="EN")


@st.cache_data(ttl=300)
def load_active_thresholds() -> dict[str, float]:
    """Load categorization thresholds from the database (falls back to hardcoded constants).

    Returns:
        Dict with keys: confidence_threshold, gap_threshold, eff_threshold.
    """
    return _load_thresholds()
