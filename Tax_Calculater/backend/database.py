"""Database configuration and session management"""
import os
from sqlalchemy import create_engine, Column, Integer, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file in the backend directory, no matter where the command is run
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Database URL from environment variables (no SQLite fallback)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env file")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db():
    """Database dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

