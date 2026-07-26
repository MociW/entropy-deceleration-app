"""
File router.

Provides template file downloads for users to understand the expected
data format before uploading to the research or config endpoints.

Routes:
    GET /file/template-file          — Download research data input template.
    GET /file/template-file-keyword  — Download keyword configuration template.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/file", tags=["File"])

# Resolve template file paths relative to the project root
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "files"
_RESEARCH_TEMPLATE = _TEMPLATES_DIR / "template-input-data.xlsx"
_KEYWORD_TEMPLATE = _TEMPLATES_DIR / "template-keyword-data.xlsx"


@router.get("/template-file")
def download_research_template():
    """
    Download the research data input template (Excel).

    Use this file as a reference for the correct column format when uploading
    data to POST /research/register.
    """
    if not _RESEARCH_TEMPLATE.exists():
        raise HTTPException(status_code=404, detail="Research template file not found on server")

    return FileResponse(
        path=str(_RESEARCH_TEMPLATE),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="template-input-data.xlsx",
    )


@router.get("/template-file-keyword")
def download_keyword_template():
    """
    Download the keyword configuration template (Excel).

    Use this file as a reference for the correct column format when uploading
    keywords to POST /config/keyword.

    Expected columns: Keyword, Group, Language (e.g., ID or EN).
    """
    if not _KEYWORD_TEMPLATE.exists():
        raise HTTPException(status_code=404, detail="Keyword template file not found on server")

    return FileResponse(
        path=str(_KEYWORD_TEMPLATE),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="template-keyword-data.xlsx",
    )
