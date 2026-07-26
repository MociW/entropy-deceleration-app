import argparse

from app.core.database import SessionLocal, init_db
from app.core.logger import configure_logging
from app.util.keyword_store import (
    load_thresholds,
    load_cue_words,
    remove_efficiency_keyword,
    add_cue_word,
    update_threshold,
    KNOWN_THRESHOLD_KEYS,
)
from app.models import (
    EfficiencyKeywordGroup,
    Research,
)


def cmd_keyword_add_cue(args):
    session = SessionLocal()
    try:
        add_cue_word(args.word, session)
        print(f"Added cue word: '{args.word}'")
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
    from app.util.cleaner import sanitize_casing

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
    from app.util.seeder import seed_config
    seed_config()


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



    # --- keyword ---
    kw = sub.add_parser("keyword", help="Manage keywords and thresholds")
    kw_sub = kw.add_subparsers(dest="kw_command")

    add_cue = kw_sub.add_parser("add-cue", help="Add an efficiency cue word")
    add_cue.add_argument("word", type=str, help="The cue word to add")
    add_cue.set_defaults(func=cmd_keyword_add_cue)


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
