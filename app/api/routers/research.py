"""
Research router.

HTTP entry points for research data ingestion and ML categorization.
All business logic is delegated to app.services.research.

Routes:
    POST /research/register    — Upload Excel, ingest raw records into the database.
    POST /research/categorize  — Trigger ML categorization on stored database records.
"""
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.services.research import ingest_research_file, categorize_research

router = APIRouter(prefix="/research", tags=["Research"])


@router.post("/register")
async def register_research_data(
    file: UploadFile = File(..., description="Excel file following the template-input-data.xlsx format"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Ingest raw research records from an uploaded Excel file into the database.

    The dataset_type (e.g. 'research', 'community_service') is read directly
    from the 'Field' column inside the uploaded file — no separate form field needed.

    Existing records for each detected dataset_type are replaced on every upload (idempotent).
    """
    suffix = Path(file.filename).suffix if file.filename else ".xlsx"
    tmp_path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = ingest_research_file(tmp_path=tmp_path, db=db)
        return {
            "message": "Research data registered successfully",
            "records_created": result.records_created,
            "dataset_types": result.dataset_types,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/categorize")
async def run_research_categorization(
    dataset_type: str = Form("research", description="Dataset category to categorize, e.g. 'research' or 'community_service'"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Run the ML categorization pipeline on all research records stored in the database.

    Loads records from the database, runs the Sentence Transformer model,
    updates the categorization results in-place, and saves output files.

    Can be triggered multiple times — each run overwrites the previous categorization results.
    """
    try:
        result = categorize_research(dataset_type=dataset_type, db=db)

        if result.records_updated == 0:
            return {
                "message": "No records found to categorize",
                "dataset_type": result.dataset_type,
                "records_updated": 0,
            }

        return {
            "message": "Categorization completed successfully",
            "dataset_type": result.dataset_type,
            "records_updated": result.records_updated,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
