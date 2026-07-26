"""
Config service layer.

Contains all business logic for keyword and keyword group management.
This layer is called exclusively by the config API router and has no HTTP concerns.

Public functions:
    bulk_import_keywords(tmp_path, db)         — Parse keyword Excel and persist new keywords.
    create_or_update_keyword_group(order, label, db) — Upsert a keyword group.
"""
from dataclasses import dataclass

import pandas as pd
from sqlalchemy.orm import Session

from app.util.keyword_store import (
    add_efficiency_keyword,
    add_efficiency_keyword_group,
)
from app.models import EfficiencyKeywordGroup


# ── Response data classes ──────────────────────────────────────────────────────

@dataclass
class KeywordImportResult:
    keywords_added: int
    rows_skipped: int


@dataclass
class KeywordGroupResult:
    group_order: int
    label: str


# ── Exceptions ─────────────────────────────────────────────────────────────────

class InvalidKeywordTemplateError(ValueError):
    """Raised when the uploaded keyword file is missing required columns."""
    pass


# ── Service functions ──────────────────────────────────────────────────────────

def bulk_import_keywords(tmp_path: str, db: Session) -> KeywordImportResult:
    """Parse an uploaded keyword Excel file and persist new efficiency keywords.

    Validates that the file contains the required columns (Keyword, Group, Language),
    then cross-references the Group column against registered keyword groups in the
    database. Rows with unknown groups or empty values are skipped gracefully.

    Args:
        tmp_path: Absolute path to the temporarily stored uploaded file.
        db:       Active SQLAlchemy database session.

    Returns:
        KeywordImportResult with counts of added and skipped rows.

    Raises:
        InvalidKeywordTemplateError: If required columns are missing from the file.
        Exception: For any unexpected database or I/O errors.
    """
    # 1. Read and normalize the uploaded Excel file
    df = pd.read_excel(tmp_path)
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Validate required columns are present
    required = {"Keyword", "Group", "Language"}
    missing = required - set(df.columns)
    if missing:
        raise InvalidKeywordTemplateError(
            f"File is missing required columns: {', '.join(sorted(missing))}. "
            "Please use the official template from GET /file/template-file-keyword."
        )

    # 3. Build a lookup map of {group_label -> group_order} from registered groups
    groups = db.query(EfficiencyKeywordGroup).all()
    group_label_to_order: dict[str, int] = {
        str(g.label).strip().lower(): int(g.group_order)  # type: ignore[arg-type]
        for g in groups
    }

    # 4. Process each row — add valid keywords, skip invalid ones
    added = 0
    skipped = 0

    for _, row in df.iterrows():
        keyword = str(row.get("Keyword", "")).strip()
        group_label = str(row.get("Group", "")).strip().lower()

        if not keyword or not group_label or keyword == "nan":
            skipped += 1
            continue

        group_order = group_label_to_order.get(group_label)
        if group_order is None:
            skipped += 1
            continue

        add_efficiency_keyword(group_order=group_order, keyword=keyword, session=db)
        added += 1

    return KeywordImportResult(keywords_added=added, rows_skipped=skipped)


def create_or_update_keyword_group(order: int, label: str, db: Session) -> KeywordGroupResult:
    """Register a new keyword group or update the label of an existing one.

    Groups are identified by their integer order. If a group with the given order
    already exists, its label is updated. This operation is idempotent.

    Args:
        order: Unique integer order/index for the group (e.g., 0, 1, 2).
        label: Human-readable group label (e.g., 'energy', 'environment').
        db:    Active SQLAlchemy database session.

    Returns:
        KeywordGroupResult with the persisted order and label.

    Raises:
        Exception: For any unexpected database errors.
    """
    add_efficiency_keyword_group(group_order=order, label=label, session=db)

    return KeywordGroupResult(group_order=order, label=label)
