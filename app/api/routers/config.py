"""
Config router.

HTTP entry points for keyword and keyword group management.
All business logic is delegated to app.services.config.

Routes:
    POST /config/keyword        — Upload keyword Excel file to add new efficiency keywords.
    POST /config/keyword-group  — Register a new efficiency keyword group.
"""
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.services.config import (
    bulk_import_keywords,
    create_or_update_keyword_group,
    InvalidKeywordTemplateError,
)

router = APIRouter(prefix="/config", tags=["Config"])


@router.post("/keyword")
async def upload_efficiency_keywords(
    file: UploadFile = File(..., description="Excel file following the template-keyword-data.xlsx format"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Upload an Excel file to add new efficiency keywords to the database.

    The file must follow the keyword template format with columns:
    - **Keyword**: The keyword text (plain text, no special characters).
    - **Group**: The keyword group label (e.g., energy, environment, infrastructure).
      The group must already be registered in the database via POST /config/keyword-group.
    - **Language**: Language code — either 'ID' (Indonesian) or 'EN' (English).

    Rows with invalid or unrecognized Group values are skipped.
    """
    suffix = Path(file.filename).suffix if file.filename else ".xlsx"
    tmp_path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = bulk_import_keywords(tmp_path=tmp_path, db=db)
        return {
            "message": "Keywords uploaded successfully",
            "keywords_added": result.keywords_added,
            "rows_skipped": result.rows_skipped,
        }
    except InvalidKeywordTemplateError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/keyword-group")
async def register_keyword_group(
    order: int = Form(..., description="Unique integer order/index for the group (e.g., 0, 1, 2)"),
    label: str = Form(..., description="Human-readable group label (e.g., 'energy', 'environment')"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Register a new efficiency keyword group, or update the label of an existing one.

    Groups are referenced by their **order** integer. If a group with the given order
    already exists, its label will be updated. This is idempotent.

    The registered group label is then used as the valid **Group** value when
    uploading keywords via POST /config/keyword.
    """
    try:
        result = create_or_update_keyword_group(order=order, label=label, db=db)
        return {
            "message": "Keyword group registered successfully",
            "group_order": result.group_order,
            "label": result.label,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
