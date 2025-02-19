# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings

# Convert PostgresDsn to string for SQLAlchemy
database_url = str(settings.database_url)

# Using SQLAlchemy 2.0 style "future" flag for modern usage.
engine = create_engine(database_url, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for database sessions
def get_db():
    """
    Dependency function that provides a SQLAlchemy session.
    Ensures proper session lifecycle for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()