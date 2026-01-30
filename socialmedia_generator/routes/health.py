"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from socialmedia_generator.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: DBSession = Depends(get_db)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
