"""
Database seeding utilities — populate configuration tables from JSON seed files.

This module is the only place that knows about the relationship between
the JSON files in ``data/`` and the database tables they populate.
The CLI is just a thin wrapper that calls ``seed_config()``.
"""
import json
import logging
from pathlib import Path

from app.core.database import SessionLocal, init_db
from app.models import (
    CategorizationConfig,
    Field,
    EfficiencyKeywordGroup,
    EfficiencyKeyword,
)

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path("data")


def seed_config(data_dir: Path | str | None = None) -> None:
    """Seed all database configuration tables from JSON seed files.

    Seeds three tables in order:
    1. ``categorization_config`` — confidence/gap/eff thresholds.
    2. ``fields`` — category names and their keyword descriptions.
    3. ``efficiency_keyword_groups`` / ``efficiency_keywords`` — EN + ID keywords.

    Args:
        data_dir: Directory containing the seed JSON files.
                  Defaults to ``data/`` relative to the current working directory.
    """
    data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    init_db()

    session = SessionLocal()
    try:
        _seed_categorization_config(session, data_dir)
        _seed_fields(session, data_dir)
        _seed_efficiency_keywords(session, data_dir)
        session.commit()
        print("Successfully seeded all configuration data to database.")
    except Exception as e:
        session.rollback()
        logger.error("Error seeding database config: %s", e)
        print(f"Error seeding database config: {e}")
    finally:
        session.close()


# ── Private helpers ────────────────────────────────────────────────────────────

def _seed_categorization_config(session, data_dir: Path) -> None:
    config_path = data_dir / "categorization_config.json"
    if not config_path.exists():
        print(f"Warning: {config_path} not found.")
        return

    with open(config_path) as f:
        config_data = json.load(f)

    for threshold in config_data.get("thresholds", []):
        key = threshold["key"]
        value = threshold["value"]
        desc = threshold.get("description", "")
        existing = session.query(CategorizationConfig).filter_by(key=key).first()
        if existing:
            existing.value = value
            existing.description = desc
        else:
            session.add(CategorizationConfig(key=key, value=value, description=desc))

    print("Categorization config loaded.")


def _seed_fields(session, data_dir: Path) -> None:
    fields_path = data_dir / "fields.json"
    if not fields_path.exists():
        print(f"Warning: {fields_path} not found.")
        return

    with open(fields_path) as f:
        fields_data = json.load(f)

    for field in fields_data.get("fields", []):
        name = field["name"]
        keywords = field["keywords"]
        existing = session.query(Field).filter_by(name=name).first()
        if existing:
            existing.keywords = keywords
        else:
            session.add(Field(name=name, keywords=keywords))

    print("Field keywords loaded.")


def _seed_efficiency_keywords(session, data_dir: Path) -> None:
    en_path = data_dir / "entropy_field_v2.json"
    id_path = data_dir / "entropy_field_v2_id.json"

    en_eff_data: dict = {}
    id_eff_data: dict = {}

    if en_path.exists():
        with open(en_path) as f:
            en_eff_data = json.load(f)
    if id_path.exists():
        with open(id_path) as f:
            id_eff_data = json.load(f)

    all_groups = set(list(en_eff_data.keys()) + list(id_eff_data.keys()))
    if not all_groups:
        print("Warning: No efficiency keyword files found.")
        return

    # Clear existing data to avoid duplicates on re-seed
    session.query(EfficiencyKeyword).delete()
    session.query(EfficiencyKeywordGroup).delete()
    session.commit()

    logical_order = ["Energy", "Environment", "Infrastructure", "Industry", "Information", "Academic"]
    groups_to_add = [g for g in logical_order if g in all_groups]
    for g in all_groups:
        if g not in groups_to_add:
            groups_to_add.append(g)

    for idx, group_label in enumerate(groups_to_add):
        group = EfficiencyKeywordGroup(group_order=idx, label=group_label)
        session.add(group)
        session.flush()

        for kw in en_eff_data.get(group_label, []):
            session.add(EfficiencyKeyword(group_id=group.id, keyword=kw, language="EN"))
        for kw in id_eff_data.get(group_label, []):
            session.add(EfficiencyKeyword(group_id=group.id, keyword=kw, language="ID"))

    loaded_files = [p.name for p in (en_path, id_path) if p.exists()]
    print(f"Efficiency keyword groups loaded with language tags (EN/ID) from: {', '.join(loaded_files)}.")
