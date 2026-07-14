import argparse
import logging
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.logging import configure_logging
from app.services.keyword_store import (
    load_thresholds,
    load_efficiency_keywords,
    load_cue_words,
    add_efficiency_keyword_group,
    add_efficiency_keyword,
    remove_efficiency_keyword,
    add_cue_word,
    update_threshold,
    KNOWN_THRESHOLD_KEYS,
)
from app.models.models import (
    CategorizationConfig,
    EfficiencyKeywordGroup,
    EfficiencyKeyword,
    Research,
)


def _fallback_eff_keywords():
    eff_kw = load_efficiency_keywords()
    print(f"\n--- Efficiency Keyword Groups ({len(eff_kw)}) (from constants fallback) ---")
    for i, kw in enumerate(eff_kw):
        preview = kw[:80] + "..." if len(kw) > 80 else kw
        print(f"  [{i}] {preview}")


def cmd_categorize(args):
    from app.services.categorizer import (
        ResearchCategorizer,
        load_data,
        preprocess,
        save_outputs,
        save_to_db,
        load_config,
    )

    init_db()

    # 1. Load raw data
    df = load_data(args.file)

    # 2. Preprocess — sanitize casing, clean titles, extract categorization texts
    df, texts = preprocess(df)

    # 3. Load ML config from DB (or constants fallback)
    config = load_config()

    # 4. Categorize — pure ML, no DB, no I/O
    categorizer = ResearchCategorizer(config=config)
    results = categorizer.categorize(texts)

    # 5. Attach results to dataframe
    df["category"] = [r["category"] for r in results]
    df["status"] = [r["status"] for r in results]
    df["confidence_score"] = [r["confidence_score"] for r in results]
    df["alt_category"] = [r["alt_category"] for r in results]
    df["alt_score"] = [r["alt_score"] for r in results]
    df["gap"] = [r["gap"] for r in results]
    df["reason"] = [r["reason"] for r in results]
    df["is_efficiency"] = [r["is_efficiency"] for r in results]
    df["efficiency_score"] = [r["efficiency_score"] for r in results]

    # 6. Save to CSV/Excel files
    save_outputs(df, Path(args.out), args.out_filename)

    # 7. Save to database
    session = SessionLocal()
    try:
        count = save_to_db(df, args.dataset_type, session)
        print(f"  Saved {count} records to SQLite (contribution_category='{args.dataset_type}')")
    except Exception as e:
        session.rollback()
        print(f"  Warning: failed to save to database: {e}")
    finally:
        session.close()


def cmd_keyword_add_cue(args):
    session = SessionLocal()
    try:
        add_cue_word(args.word, session)
        print(f"Added cue word: '{args.word}'")
    finally:
        session.close()


def cmd_keyword_add_group(args):
    session = SessionLocal()
    try:
        add_efficiency_keyword_group(args.order, args.label, session)
        print(f"Added/updated efficiency group {args.order}: '{args.label}'")
    finally:
        session.close()


def cmd_keyword_add_efficiency(args):
    session = SessionLocal()
    try:
        add_efficiency_keyword(args.order, args.keyword, session)
        print(f"Added keyword '{args.keyword}' to group {args.order}")
    finally:
        session.close()


def cmd_keyword_remove_efficiency(args):
    session = SessionLocal()
    try:
        removed = remove_efficiency_keyword(args.id, session)
        if removed:
            print(f"Removed keyword {args.id}")
        else:
            print(f"Keyword {args.id} not found")
    finally:
        session.close()

def cmd_keyword_set_threshold(args):
    """Update a single threshold value in the database (upsert)."""
    try:
        row = update_threshold(key=args.key, value=args.value)
        print(f"✓  {row.key} = {row.value}")
        if row.description:
            print(f"   {row.description}")
    except ValueError as e:
        print(f"Error: {e}")
        raise SystemExit(1)
    except Exception as e:
        print(f"Database error: {e}")
        raise SystemExit(1)


def cmd_keyword_list(args):
    thresholds = load_thresholds()
    print("--- Thresholds ---")
    for k, v in thresholds.items():
        print(f"  {k}: {v}")

    session = SessionLocal()
    try:
        groups = session.query(EfficiencyKeywordGroup).order_by(EfficiencyKeywordGroup.group_order).all()
        if groups:
            print(f"\n--- Efficiency Keywords ({len(groups)} groups) ---")
            for group in groups:
                kw_list = [k.keyword for k in group.keywords]
                print(f"  [{group.group_order}] {group.label} ({len(kw_list)} keywords)")
                for k in group.keywords:
                    print(f"       {k.id}  {k.keyword}")
        else:
            _fallback_eff_keywords()
    except Exception:
        _fallback_eff_keywords()
    finally:
        session.close()

    cue_words = load_cue_words()
    print(f"\n--- Cue Words ({len(cue_words)}) ---")
    print(f"  {', '.join(cue_words)}")


def cmd_initdb(args):
    """Initialize/create all database tables."""
    init_db()
    print("Database tables created successfully.")


def cmd_sanitize_db(args):
    """Sanitize titles and abstracts of existing records in the database."""
    from app.services.cleaner import sanitize_casing
    session = SessionLocal()
    try:
        researches = session.query(Research).all()
        print(f"Sanitizing casing for {len(researches)} database records...")
        updated_count = 0
        for r in researches:
            orig_title = r.title
            orig_abstract = r.abstract

            san_title = sanitize_casing(orig_title)
            san_abstract = sanitize_casing(orig_abstract) if orig_abstract else None

            if san_title != orig_title or san_abstract != orig_abstract:
                r.title = san_title
                r.abstract = san_abstract
                updated_count += 1

        if updated_count > 0:
            session.commit()
            print(f"Successfully sanitized casing for {updated_count} records.")
        else:
            print("No records required casing sanitization.")
    except Exception as e:
        session.rollback()
        print(f"Error during sanitization: {e}")
    finally:
        session.close()


def cmd_seed_config(args):
    """Seed database configuration tables (configs, fields, and efficiency keywords)."""
    import json
    from pathlib import Path
    from app.models.models import CategorizationConfig, Field, EfficiencyKeywordGroup, EfficiencyKeyword

    # Ensure tables exist
    init_db()

    session = SessionLocal()
    data_dir = Path("data")
    try:
        # 1. Seed categorization thresholds
        config_path = data_dir / "categorization_config.json"
        if config_path.exists():
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
        else:
            print(f"Warning: {config_path} not found.")

        # 2. Seed fields/category descriptors
        fields_path = data_dir / "fields.json"
        if fields_path.exists():
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
        else:
            print(f"Warning: {fields_path} not found.")

        # 3. Seed both English (EN) and Indonesian (ID) keyword lists
        en_path = data_dir / "entropy_field_v2.json"
        id_path = data_dir / "entropy_field_v2_id.json"

        en_eff_data = {}
        id_eff_data = {}

        if en_path.exists():
            with open(en_path) as f:
                en_eff_data = json.load(f)

        if id_path.exists():
            with open(id_path) as f:
                id_eff_data = json.load(f)

        all_groups = set(list(en_eff_data.keys()) + list(id_eff_data.keys()))

        if all_groups:
            # Clear existing efficiency keywords & groups to avoid duplicates
            session.query(EfficiencyKeyword).delete()
            session.query(EfficiencyKeywordGroup).delete()
            session.commit()

            # Preserve standard logical order
            logical_order = ["Energy", "Environment", "Infrastructure", "Industry", "Information","Academic"]
            groups_to_add = [g for g in logical_order if g in all_groups]
            for g in all_groups:
                if g not in groups_to_add:
                    groups_to_add.append(g)

            for idx, group_label in enumerate(groups_to_add):
                group = EfficiencyKeywordGroup(group_order=idx, label=group_label)
                session.add(group)
                session.flush() # Populate group.id

                # Load English keywords
                en_kws = en_eff_data.get(group_label, [])
                for kw in en_kws:
                    session.add(EfficiencyKeyword(group_id=group.id, keyword=kw, language="EN"))

                # Load Indonesian keywords
                id_kws = id_eff_data.get(group_label, [])
                for kw in id_kws:
                    session.add(EfficiencyKeyword(group_id=group.id, keyword=kw, language="ID"))

            loaded_files = []
            if en_path.exists(): loaded_files.append(en_path.name)
            if id_path.exists(): loaded_files.append(id_path.name)
            print(f"Efficiency keyword groups loaded with language tags (EN/ID) from: {', '.join(loaded_files)}.")
        else:
            print("Warning: No efficiency keyword files found.")

        session.commit()
        print("Successfully seeded all configuration data to database.")
    except Exception as e:
        session.rollback()
        print(f"Error seeding database config: {e}")
    finally:
        session.close()


def main():
    configure_logging()
    parser = argparse.ArgumentParser(description="Entropi Research Categorizer")
    sub = parser.add_subparsers(dest="command")

    # --- init-db ---
    init_parser = sub.add_parser("init-db", help="Initialize database tables")
    init_parser.set_defaults(func=cmd_initdb)

    # --- sanitize-db ---
    sanitize_parser = sub.add_parser("sanitize-db", help="Sanitize casing of titles/abstracts in database")
    sanitize_parser.set_defaults(func=cmd_sanitize_db)

    # --- seed-config ---
    seed_config_parser = sub.add_parser("seed-config", help="Seed configuration from JSON files")
    seed_config_parser.set_defaults(func=cmd_seed_config)

    # --- categorize ---
    cat = sub.add_parser("categorize", help="Run categorization on a file")
    cat.add_argument("--file", type=str, required=True, help="Path to CSV or XLSX file")
    cat.add_argument("--out", type=str, default=settings.OUTPUT_DIR)
    cat.add_argument("--out_filename", type=str, default="Hasil_Analisis_Proyek_Penelitian_V5_0")
    cat.add_argument(
        "--dataset_type", type=str, default="research",
        help="Dataset type label, e.g. 'research' or 'community_service'"
    )
    cat.set_defaults(func=cmd_categorize)

    # --- keyword ---
    kw = sub.add_parser("keyword", help="Manage keywords and thresholds")
    kw_sub = kw.add_subparsers(dest="kw_command")

    add_cue = kw_sub.add_parser("add-cue", help="Add an efficiency cue word")
    add_cue.add_argument("word", type=str, help="The cue word to add")
    add_cue.set_defaults(func=cmd_keyword_add_cue)

    add_group = kw_sub.add_parser("add-group", help="Add/update an efficiency keyword group")
    add_group.add_argument("--order", type=int, required=True, help="Group order/index (e.g. 0-6)")
    add_group.add_argument("--label", type=str, required=True, help="Group label")
    add_group.set_defaults(func=cmd_keyword_add_group)

    add_eff = kw_sub.add_parser("add-efficiency", help="Add a single keyword to an efficiency group")
    add_eff.add_argument("--order", type=int, required=True, help="Target group order/index")
    add_eff.add_argument("--keyword", type=str, required=True, help="The keyword to add")
    add_eff.set_defaults(func=cmd_keyword_add_efficiency)

    rm_eff = kw_sub.add_parser("remove-efficiency", help="Remove a single keyword by its ID")
    rm_eff.add_argument("--id", type=str, required=True, help="Keyword ID to remove")
    rm_eff.set_defaults(func=cmd_keyword_remove_efficiency)

    set_th = kw_sub.add_parser("set-threshold", help="Update a categorization threshold in the database")
    set_th.add_argument(
        "--key",
        type=str,
        required=True,
        choices=sorted(KNOWN_THRESHOLD_KEYS),
        metavar="KEY",
        help=f"Threshold key to update. One of: {', '.join(sorted(KNOWN_THRESHOLD_KEYS))}",
    )
    set_th.add_argument("--value", type=float, required=True, help="New threshold value (float >= 0)")
    set_th.set_defaults(func=cmd_keyword_set_threshold)

    list_kw = kw_sub.add_parser("list", help="List all keywords and thresholds")
    list_kw.set_defaults(func=cmd_keyword_list)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
