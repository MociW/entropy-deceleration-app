"""
Data loading and preprocessing layer for the categorization pipeline.

Reads raw Excel/CSV files, sanitizes text, and extracts the strings
that will be passed to the ML model. No database or Streamlit interaction.
"""
from pathlib import Path

import pandas as pd

from sqlalchemy.orm import Session

from app.models import Research
from app.util.cleaner import clean_title, sanitize_casing


def research_load_data(path: str) -> pd.DataFrame:
    """Load a research data file (CSV or Excel) and normalize column names.

    Ensures ``title`` column exists. Adds empty ``year`` column if absent.
    Returns only the columns that are used downstream.

    Args:
        path: Absolute or relative path to a ``.csv``, ``.xlsx``, or ``.xls`` file.

    Returns:
        DataFrame with at minimum ``title`` and ``year`` columns.

    Raises:
        ValueError: If the file has no ``title`` column.
    """
    p = Path(path)
    df = pd.read_excel(p) if p.suffix in {".xlsx", ".xls"} else pd.read_csv(p)
    df.columns = [c.strip().lower() for c in df.columns]

    if "title" not in df.columns:
        raise ValueError("File must have a 'title' column.")
    if "year" not in df.columns:
        df["year"] = None

    cols = ["title", "year"]
    for c in ("abstract", "author", "institution", "field", "start_at", "finish_at"):
        if c in df.columns:
            cols.append(c)

    res_df = df[cols].copy()
    if "abstract" in res_df.columns:
        res_df["abstract"] = res_df["abstract"].fillna("")
    return res_df


def research_preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Sanitize casing and clean titles; extract categorization texts.

    Args:
        df: Raw DataFrame from ``research_load_data``.

    Returns:
        A tuple of (clean_df, texts) where ``texts`` is the list of strings
        to pass directly to ``ResearchCategorizer.categorize``.
    """
    df = df.copy()
    df["title"] = df["title"].apply(sanitize_casing)
    if "abstract" in df.columns:
        df["abstract"] = df["abstract"].apply(sanitize_casing)

    # df["title"] = df["title"].apply(clean_title)
    texts = [clean_title(t) for t in get_categorization_texts(df)]
    return df, texts


def get_categorization_texts(df: pd.DataFrame) -> list[str]:
    """Return abstract if present and non-empty (> 10 chars), else title.

    Args:
        df: DataFrame with at minimum a ``title`` column.

    Returns:
        List of strings — one per row — to use as categorization input.
    """
    if "abstract" not in df.columns:
        return df["title"].tolist()

    texts = []
    for _, row in df.iterrows():
        abstract = str(row.get("abstract", "")).strip()
        title = str(row["title"]).strip()
        texts.append(abstract if abstract and len(abstract) > 10 else title)
    return texts


def load_uncategorized_from_db(dataset_type: str, session: Session) -> tuple[pd.DataFrame, list[str]]:
    """Query the database for research records to be categorized.

    Args:
        dataset_type: The contribution category (e.g., 'research').
        session: Active SQLAlchemy session.

    Returns:
        A tuple of (clean_df, texts). The clean_df contains at least the 'id', 'title',
        'abstract', and 'year' columns, which are required for updating the DB and exporting.
        The 'texts' list is ready for the ML model.
    """
    records = session.query(Research).filter_by(contribution_category=dataset_type).all()

    data = []
    for r in records:
        data.append({
            "id": r.id,
            "title": r.title,
            "abstract": r.abstract or "",
            "year": r.year,
        })

    df = pd.DataFrame(data)
    if df.empty:
        return df, []

    return preprocess(df)
