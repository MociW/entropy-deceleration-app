"""
Research service layer.

Contains all business logic for research data ingestion and ML categorization.
This layer is called exclusively by the research API router and has no HTTP concerns.

Public functions:
    ingest_research_file(tmp_path, db)   — Load, preprocess, and store raw records.
    categorize_research(dataset_type, db) — Run ML pipeline and persist results.
"""
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.util.pipeline import (
    research_load_data,
    research_preprocess,
    create_research_records,
    load_uncategorized_from_db,
    load_config,
    ResearchCategorizer,
    update_categorization_results,
    save_outputs,
)
from app.core.config import settings


# ── Response data classes ──────────────────────────────────────────────────────

@dataclass
class ResearchIngestionResult:
    records_created: int
    dataset_types: list[str]


@dataclass
class ResearchCategorizationResult:
    dataset_type: str
    records_updated: int


# ── Service functions ──────────────────────────────────────────────────────────

def ingest_research_file(tmp_path: str, db: Session) -> ResearchIngestionResult:
    """Load an uploaded research file, preprocess it, and persist raw records.

    Reads the dataset_type directly from the 'field' column inside the file.
    Only registers/appends raw data to the database without purging existing records.

    Args:
        tmp_path: Absolute path to the temporarily stored uploaded file.
        db:       Active SQLAlchemy database session.

    Returns:
        ResearchIngestionResult with counts and detected dataset types.

    Raises:
        ValueError: If the file is missing required columns.
        Exception:  For any unexpected database or I/O errors.
    """
    # 1. Load and normalize column names
    df = research_load_data(tmp_path)

    # 2. Sanitize text (casing, title cleaning)
    df, _ = research_preprocess(df)

    # 3. Persist raw records — dataset_type is read from df['field']
    count = create_research_records(df, db)

    dataset_types = (
        df["field"].dropna().unique().tolist() if "field" in df.columns else []
    )

    return ResearchIngestionResult(
        records_created=count,
        dataset_types=dataset_types,
    )


def categorize_research(dataset_type: str, db: Session) -> ResearchCategorizationResult:
    """Run the ML categorization pipeline on research records stored in the database.

    Loads all records for the given dataset_type, runs the Sentence Transformer,
    updates categorization flags in the database, and exports output files.

    Can be called multiple times — each run overwrites the previous results.

    Args:
        dataset_type: The contribution category to categorize (e.g., 'research').
        db:           Active SQLAlchemy database session.

    Returns:
        ResearchCategorizationResult with the count of updated records.

    Raises:
        ValueError: If no records are found for the given dataset_type.
        Exception:  For any unexpected model or database errors.
    """
    # 1. Load records from the database for the target dataset_type
    df, texts = load_uncategorized_from_db(dataset_type, db)

    if df.empty:
        return ResearchCategorizationResult(
            dataset_type=dataset_type,
            records_updated=0,
        )

    # 2. Load ML thresholds and configuration from the database
    config = load_config()

    # 3. Run the Sentence Transformer model
    categorizer = ResearchCategorizer(config=config)
    results = categorizer.categorize(texts)

    # 4. Attach ML output columns to the DataFrame
    df["category"] = [r["category"] for r in results]
    df["status"] = [r["status"] for r in results]
    df["confidence_score"] = [r["confidence_score"] for r in results]
    df["alt_category"] = [r["alt_category"] for r in results]
    df["alt_score"] = [r["alt_score"] for r in results]
    df["gap"] = [r["gap"] for r in results]
    df["reason"] = [r["reason"] for r in results]
    df["is_efficiency"] = [r["is_efficiency"] for r in results]
    df["efficiency_score"] = [r["efficiency_score"] for r in results]

    # 5. Persist categorization results back to the database
    count = update_categorization_results(df, db)

    # 6. Export results to CSV and Excel output files
    out_dir = Path(settings.OUTPUT_DIR)
    out_filename = "Hasil_Analisis_Proyek_Penelitian_V5_0"
    save_outputs(df, out_dir, out_filename)

    return ResearchCategorizationResult(
        dataset_type=dataset_type,
        records_updated=count,
    )
