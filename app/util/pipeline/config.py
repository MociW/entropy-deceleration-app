"""
Categorization pipeline — CategorizerConfig dataclass and its DB-backed factory.

This module is the configuration boundary between the keyword/threshold store
(app.services.keyword_store) and the ML inference layer (pipeline.model).
No I/O or UI code should live here.
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.util.keyword_store import (
    load_thresholds,
    load_field_keywords,
    load_efficiency_keywords,
    load_cue_words,
)


@dataclass
class CategorizerConfig:
    """Immutable snapshot of all tuneable parameters needed by ResearchCategorizer."""

    confidence_threshold: float
    gap_threshold: float
    eff_threshold: float
    field_names: list[str]
    field_descriptions: list[str]
    efficiency_keywords_en: list[str] | None
    efficiency_keywords_id: list[str] | None
    efficiency_cue_words: list[str]


def load_config(session: Session | None = None) -> CategorizerConfig:
    """Build a CategorizerConfig from the database (falls back to hardcoded constants).

    Args:
        session: Optional existing SQLAlchemy session. A new one is opened if None.

    Returns:
        A fully populated CategorizerConfig ready to pass to ResearchCategorizer.
    """
    thresholds = load_thresholds(session)
    fields = load_field_keywords(session)
    eff_kw_en = load_efficiency_keywords(lang="EN", session=session)
    eff_kw_id = load_efficiency_keywords(lang="ID", session=session)
    cue_words = load_cue_words(session)

    return CategorizerConfig(
        confidence_threshold=thresholds["confidence_threshold"],
        gap_threshold=thresholds["gap_threshold"],
        eff_threshold=thresholds["eff_threshold"],
        field_names=list(fields.keys()),
        field_descriptions=list(fields.values()),
        efficiency_keywords_en=eff_kw_en if eff_kw_en else None,
        efficiency_keywords_id=eff_kw_id if eff_kw_id else None,
        efficiency_cue_words=cue_words,
    )
