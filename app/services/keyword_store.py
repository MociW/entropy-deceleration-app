import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.database import SessionLocal
from app.models.models import (
    CategorizationConfig,
    EfficiencyKeywordGroup,
    EfficiencyKeyword,
    EfficiencyCueWord,
    Field as FieldModel,
)
from app.services.constants import (
    FIELDS,
    EFFICIENCY_KEYWORDS,
    EFFICIENCY_CUE_WORDS,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_GAP_THRESHOLD,
    DEFAULT_EFF_THRESHOLD,
)


def _get_session() -> Session:
    return SessionLocal()


def load_thresholds(session: Session | None = None) -> dict[str, float]:
    defaults = {
        "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        "gap_threshold": DEFAULT_GAP_THRESHOLD,
        "eff_threshold": DEFAULT_EFF_THRESHOLD,
    }
    try:
        close_session = session is None
        session = session or _get_session()
        rows = session.query(CategorizationConfig).all()
        if rows:
            for r in rows:
                defaults[r.key] = r.value
        if close_session:
            session.close()
    except Exception as e:
        logger.warning("Failed to load thresholds from DB, using defaults: %s", e)
    return defaults


KNOWN_THRESHOLD_KEYS = frozenset({
    "confidence_threshold",
    "gap_threshold",
    "eff_threshold",
})


def update_threshold(key: str, value: float, session: Session | None = None) -> CategorizationConfig:
    """Upsert a threshold value in the database.

    - Updates the row if the key already exists.
    - Inserts a new row if the key is not yet in the database (e.g. DB was never seeded).
    - Raises ValueError for unknown keys to catch typos early.

    Args:
        key:     One of 'confidence_threshold', 'gap_threshold', 'eff_threshold'.
        value:   The new threshold value (must be a positive float).
        session: Optional existing SQLAlchemy session. A new one is opened if not provided.

    Returns:
        The updated or newly created CategorizationConfig row.
    """
    if key not in KNOWN_THRESHOLD_KEYS:
        raise ValueError(
            f"Unknown threshold key '{key}'. "
            f"Valid keys: {', '.join(sorted(KNOWN_THRESHOLD_KEYS))}"
        )
    if value < 0:
        raise ValueError(f"Threshold value must be >= 0, got {value}")

    close_session = session is None
    session = session or _get_session()
    try:
        row = session.query(CategorizationConfig).filter_by(key=key).first()
        if row:
            old_value = row.value
            row.value = value
            logger.info("Updated threshold '%s': %s -> %s", key, old_value, value)
        else:
            # DB was not seeded — insert the row so future loads are DB-driven
            description_map = {
                "confidence_threshold": "Minimum cosine similarity score for a category to be accepted",
                "gap_threshold": "Minimum gap between top-1 and top-2 scores before marking as Ambiguous",
                "eff_threshold": "Minimum efficiency score to flag a record as Entropy-related",
            }
            row = CategorizationConfig(
                key=key,
                value=value,
                description=description_map.get(key, ""),
            )
            session.add(row)
            logger.info("Inserted new threshold '%s' = %s", key, value)
        session.commit()
        session.refresh(row)
        return row
    except Exception:
        session.rollback()
        raise
    finally:
        if close_session:
            session.close()

def load_field_keywords(session: Session | None = None) -> dict[str, str]:
    try:
        close_session = session is None
        session = session or _get_session()
        rows = session.query(FieldModel).all()
        if rows:
            result = {r.name: r.keywords for r in rows}
            if close_session:
                session.close()
            return result
        if close_session:
            session.close()
    except Exception as e:
        logger.warning("Failed to load field keywords from DB, using constants fallback: %s", e)
    return dict(FIELDS)


def load_efficiency_keywords(lang: str | None = None, session: Session | None = None) -> list[str]:
    try:
        close_session = session is None
        session = session or _get_session()
        groups = session.query(EfficiencyKeywordGroup).order_by(EfficiencyKeywordGroup.group_order).all()
        if groups:
            result = []
            for group in groups:
                if lang:
                    keywords = [k.keyword for k in group.keywords if k.language == lang]
                else:
                    keywords = [k.keyword for k in group.keywords]
                result.append(" ".join(keywords) if keywords else "")
            if close_session:
                session.close()
            return result
        if close_session:
            session.close()
    except Exception as e:
        logger.warning("Failed to load efficiency keywords from DB, using constants fallback: %s", e)
    if lang == "ID":
        return []
    return list(EFFICIENCY_KEYWORDS)


def load_cue_words(session: Session | None = None) -> list[str]:
    try:
        close_session = session is None
        session = session or _get_session()
        rows = session.query(EfficiencyCueWord).all()
        if rows:
            result = [r.word for r in rows]
            if close_session:
                session.close()
            return result
        if close_session:
            session.close()
    except Exception as e:
        logger.warning("Failed to load cue words from DB, using constants fallback: %s", e)
    return list(EFFICIENCY_CUE_WORDS)


def add_efficiency_keyword_group(
    group_order: int, label: str, session: Session | None = None
) -> EfficiencyKeywordGroup:
    close_session = session is None
    session = session or _get_session()
    existing = session.query(EfficiencyKeywordGroup).filter_by(group_order=group_order).first()
    if existing:
        existing.label = label
        group = existing
    else:
        group = EfficiencyKeywordGroup(group_order=group_order, label=label)
        session.add(group)
    session.commit()
    if close_session:
        session.close()
    return group


def add_efficiency_keyword(group_order: int, keyword: str, session: Session | None = None) -> None:
    close_session = session is None
    session = session or _get_session()

    group = session.query(EfficiencyKeywordGroup).filter_by(group_order=group_order).first()
    if not group:
        raise ValueError(f"Efficiency keyword group with order {group_order} not found.")

    existing = session.query(EfficiencyKeyword).filter_by(group_id=group.id, keyword=keyword).first()
    if not existing:
        session.add(EfficiencyKeyword(group_id=group.id, keyword=keyword))
        session.commit()

    if close_session:
        session.close()


def remove_efficiency_keyword(keyword_id: str, session: Session | None = None) -> bool:
    close_session = session is None
    session = session or _get_session()
    kw = session.query(EfficiencyKeyword).filter_by(id=keyword_id).first()
    if kw:
        session.delete(kw)
        session.commit()
        if close_session:
            session.close()
        return True
    if close_session:
        session.close()
    return False


def load_efficiency_keyword_map(lang: str | None = None, session: Session | None = None) -> dict[str, list[str]]:
    """Return {group_label: [keyword1, keyword2, ...]} from DB, optionally filtered by language."""
    try:
        close_session = session is None
        session = session or _get_session()
        groups = session.query(EfficiencyKeywordGroup).order_by(EfficiencyKeywordGroup.group_order).all()
        if groups:
            result = {}
            for group in groups:
                keywords = [k.keyword for k in group.keywords if lang is None or k.language == lang]
                if keywords:
                    result[group.label] = keywords
            if close_session:
                session.close()
            return result
        if close_session:
            session.close()
    except Exception as e:
        logger.warning("Failed to load efficiency keyword map from DB: %s", e)
    return {}


def add_cue_word(word: str, session: Session | None = None) -> None:
    close_session = session is None
    session = session or _get_session()
    existing = session.query(EfficiencyCueWord).filter_by(word=word).first()
    if not existing:
        session.add(EfficiencyCueWord(word=word))
        session.commit()
    if close_session:
        session.close()
