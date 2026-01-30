"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from .models import Base

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./computer_use_demo.db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    # Import all models to ensure they're registered
    from . import models  # Original models
    from . import post_models  # New post models
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database session.
    
    Yields:
        Database session for request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
