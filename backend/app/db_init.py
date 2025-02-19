# backend/app/db_init.py
"""
Database initialization script to create tables before application startup.
"""
import logging
from sqlalchemy import create_engine, inspect
from backend.app.config import settings
from backend.app.models.document import Base, Document

# Configure logging
logger = logging.getLogger(__name__)


def create_tables():
    """
    Create all tables defined in SQLAlchemy models if they don't exist.
    """
    # Convert PostgresDsn to string for SQLAlchemy
    database_url = str(settings.database_url)
    engine = create_engine(database_url, echo=True)

    # Check if tables exist
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if 'documents' not in existing_tables:
        logger.info("Creating documents table...")
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    else:
        logger.info("Tables already exist, skipping creation")


if __name__ == "__main__":
    # Configure logging for direct script execution
    logging.basicConfig(level=logging.INFO)
    # Can be run directly for initial database setup
    create_tables()