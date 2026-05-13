"""
Database configuration for the CCRTS application.

Uses SQLAlchemy ORM with SQLite by default. Override with the
DATABASE_URL environment variable to switch to PostgreSQL.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ccrts.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a session and ensures clean teardown."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
