"""
Database connection and session management for ViralCoin application.
This module initializes the SQLAlchemy database connection, creates tables from models,
and provides utility functions for database session management.
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database

from models import Base

# Get database URL from environment or use SQLite as default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///viralcoin.db")

# Create engine based on DATABASE_URL
engine = create_engine(DATABASE_URL, echo=os.getenv("SQL_ECHO", "false").lower() == "true")

# Create a database if it doesn't exist (mainly for PostgreSQL)
if not database_exists(engine.url) and not DATABASE_URL.startswith("sqlite:"):
    create_database(engine.url)

# Create a scoped session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def init_db():
    """
    Initialize the database by creating all tables defined in the models.
    """
    Base.metadata.create_all(engine)

def reset_db():
    """
    Reset the database by dropping all tables and creating them again.
    WARNING: This will delete all data in the database.
    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

@contextmanager
def get_session():
    """
    Context manager for database sessions.
    Provides automatic commit/rollback functionality.
    
    Usage:
    with get_session() as session:
        user = session.query(User).first()
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_db_session():
    """
    Get a database session object.
    Note: The caller is responsible for closing the session.
    
    Returns:
        SQLAlchemy session object
    """
    return Session()

def close_db_session(session):
    """
    Close a database session.
    
    Args:
        session: SQLAlchemy session object to close
    """
    if session:
        session.close()

# Initialize the database on module import
if os.getenv("AUTO_INIT_DB", "true").lower() == "true":
    init_db()

