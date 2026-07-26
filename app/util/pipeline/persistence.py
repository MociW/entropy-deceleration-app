"""
Persistence layer for the categorization pipeline.

Handles two output paths:
1. File export  — writes CSV and multi-sheet Excel files to disk.
2. Database save — upserts Research records and their validation flags.

No ML, no UI, no configuration loading lives here.
"""
import re
from pathlib import Path

import pandas as pd
from dateutil import parser as date_parser
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import cast

from app.models import (
    Research,
    ResearchValidationFlag,
    Author,
    Institution,
    research_authors,
)

# ── Column mapping ─────────────────────────────────────────────────────────────

_EXPORT_COLS = [
    "title", "year", "category", "status", "is_efficiency",
    "confidence_score", "gap", "efficiency_score",
    "alt_category", "alt_score", "reason",
]

_RENAME_MAP = {
    "title": "Title",
    "year": "Year",
    "abstract": "Abstract",
    "category": "Category",
    "status": "Status",
    "is_efficiency": "Efficiency Focus",
    "confidence_score": "Category Score",
    "gap": "Category Gap",
    "efficiency_score": "Max Efficiency Score",
    "alt_category": "Alt Category",
    "alt_score": "Alt Score",
    "reason": "Reason",
}


def _to_str(value) -> str | None:
    """Coerce a pandas scalar to str, treating NaN/None as missing."""
    if pd.isna(value):
        return None
    return str(value)


def _to_float(value) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _to_bool(value) -> bool | None:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1"}
    return bool(value)


# ── Public API ─────────────────────────────────────────────────────────────────

def save_outputs(df: pd.DataFrame, out_dir: Path, out_filename: str) -> None:
    """Export categorized DataFrame to CSV and a multi-sheet Excel workbook.

    Args:
        df:           Categorized DataFrame (output of categorizer + preprocess).
        out_dir:      Directory where output files will be written (created if needed).
        out_filename: Base filename without extension.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    export_cols = list(_EXPORT_COLS)
    if "abstract" in df.columns:
        export_cols.insert(2, "abstract")

    export = df[export_cols].copy()
    export.columns = [_RENAME_MAP.get(c, c) for c in export.columns]

    csv_path = out_dir / f"{out_filename}.csv"
    export.to_csv(csv_path, index=False)

    xlsx_path = out_dir / f"{out_filename}.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        export.to_excel(writer, index=False, sheet_name="Results")

        sum_cat = df.groupby(["category", "status"]).size().reset_index(name="Count")
        sum_cat.to_excel(writer, index=False, sheet_name="Summary_Bidang")

        sum_eff = df["is_efficiency"].value_counts().reset_index()
        sum_eff.columns = ["Efficiency Focus", "Count"]
        sum_eff.to_excel(writer, index=False, sheet_name="Summary_Efisiensi")

    print(f"\nProcess complete. Files saved to: {xlsx_path}")
    print(f"  CSV also available at: {csv_path}")


def delete_research_records(dataset_type: str, session: Session) -> int:
    """Delete all research records for the given dataset_type from the database.

    Args:
        dataset_type: The contribution category whose records will be deleted (e.g., 'research').
        session:      Active SQLAlchemy session.

    Returns:
        Number of records deleted.
    """
    existing = session.query(Research).filter_by(contribution_category=dataset_type).all()
    count = len(existing)
    for r in existing:
        session.delete(r)
    session.flush()
    return count


def create_research_records(df: pd.DataFrame, session: Session) -> int:
    """Ingest raw research records from a DataFrame into the database.

    Each record is initialized with an 'Uncategorized' validation flag.
    Does NOT delete existing records — call delete_research_records() first
    if you need to replace the existing dataset.

    Args:
        df:      Preprocessed DataFrame containing at minimum 'title', 'year', and 'field' columns.
        session: Active SQLAlchemy session.

    Returns:
        Total number of records inserted.
    """
    has_abstract: bool = "abstract" in df.columns
    has_author: bool = "author" in df.columns
    has_institution: bool = "institution" in df.columns

    author_cache: dict[str, Author] = {auth.nidn or auth.name: auth for auth in session.scalars(select(Author)).all()}
    institution_cache: dict[str, Institution] = {inst.name: inst for inst in session.scalars(select(Institution)).all()}

    for _, row in df.iterrows():
        start_at = _parse_date(row.get("start_at"))
        finish_at = _parse_date(row.get("finish_at"))
        data_id = int(row["data_id"]) if pd.notna(row.get("data_id")) and row.get("data_id") else None

        research = Research(
            data_id=data_id,
            title=row["title"],
            abstract=_to_str(row.get("abstract")) if has_abstract else None,
            year=int(row["year"]) if row["year"] else 0,
            contribution_category=row["field"],
            start_at=start_at,
            finish_at=finish_at,
        )
        # Default empty validation flag
        research.validation_flag = ResearchValidationFlag(
            status="Uncategorized"
        )
        session.add(research)
        session.flush()

        if has_institution:
            _attach_institutions(row, research, institution_cache, session)
        if has_author:
            _attach_authors(row, research, author_cache, session)

    session.commit()
    return len(df)


def update_categorization_results(results_df: pd.DataFrame, session: Session) -> int:
    """Update ResearchValidationFlag records based on ML results.

    Args:
        results_df: DataFrame containing 'id' and all ML output columns.
        session:    Active SQLAlchemy session.

    Returns:
        Number of records updated.
    """
    count = 0
    for _, row in results_df.iterrows():
        flag = session.query(ResearchValidationFlag).filter_by(research_id=row["id"]).first()
        if flag:
            flag.category = _to_str(row.get("category"))
            flag.status = _to_str(row.get("status"))
            flag.confidence_score = _to_float(row.get("confidence_score"))
            flag.alt_category = _to_str(row.get("alt_category"))
            flag.alt_score = _to_float(row.get("alt_score"))
            flag.gap = _to_float(row.get("gap"))
            flag.reason = _to_str(row.get("reason"))
            flag.is_efficiency = _to_str(row.get("is_efficiency"))
            flag.efficiency_score = _to_float(row.get("efficiency_score"))
            flag.is_entropy = (row.get("is_efficiency") == "Yes")
            count += 1

    session.commit()
    return count


# ── Private helpers ────────────────────────────────────────────────────────────

def _parse_date(value):
    """Parse a date value from a DataFrame cell; returns None on failure."""
    if pd.notna(value) and value:
        try:
            return date_parser.parse(str(value)).date()
        except Exception:
            pass
    return None


def _attach_institutions(row: pd.Series, research: Research, cache: dict[str, Institution], session: Session) -> None:
    """Look up or create Institution records and attach them to a Research row."""
    inst_str = str(row.get("institution", ""))
    if not inst_str or inst_str.lower() == "nan":
        return

    seen: set[str] = set()
    for inst_name in (i.strip() for i in inst_str.split(";") if i.strip()):
        inst = cache.get(inst_name)
        if inst is None:
            inst = Institution(name=inst_name)
            session.add(inst)
            session.flush()
            cache[inst_name] = inst
        inst_id = cast(str, cast(object, inst.id))
        if inst_id not in seen:
            research.institutions.append(inst)
            seen.add(inst_id)


def _attach_authors(row, research: Research, cache: dict, session: Session) -> None:
    """Look up or create Author records and attach them via the association table."""
    author_str = str(row.get("author", ""))
    if not author_str or author_str.lower() == "nan":
        return

    seen: set[str] = set()
    for auth_item in (a.strip() for a in author_str.split(";") if a.strip()):
        match = re.search(r"([^\[(]+)(?:\[NIDN:\s*([^]]+)])?(?:\(([^)]+)\))?", auth_item)
        if not match:
            continue

        name = match.group(1).strip()
        nidn = match.group(2).strip() if match.group(2) else None
        raw_role = match.group(3).strip() if match.group(3) else None
        role = None
        if raw_role:
            role = "Leader" if "ketua" in raw_role.lower() else (
                "Member" if "anggota" in raw_role.lower() else raw_role)

        key = nidn or name
        auth = cache.get(key)
        if auth is None:
            auth = Author(name=name, nidn=nidn)
            session.add(auth)
            session.flush()
            cache[key] = auth
        auth_id = cast(str, cast(object, auth.id))
        if auth_id not in seen:
            session.execute(
                research_authors.insert().values(
                    research_id=research.id,
                    author_id=auth.id,
                    role=role,
                )
            )
            seen.add(auth_id)
