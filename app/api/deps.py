from typing import Generator
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings

x_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key_header: str = Security(x_api_key_header)):
    """FastAPI dependency to check the API Key."""
    if api_key_header == settings.API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="could not validate API Key"
    )

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
