# db.py
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SERVER = os.getenv("AZURE_SQL_SERVER")
DATABASE = os.getenv("AZURE_SQL_DB")
USERNAME = os.getenv("AZURE_SQL_USER")
PASSWORD = os.getenv("AZURE_SQL_PASSWORD")
DATABASE_URL = (
    f"mssql+pyodbc://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Encrypt=yes"
    "&TrustServerCertificate=no"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# context manager for db session scope
@contextmanager
def _session_scope():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# generator function to be used with FastAPI's Depends
def get_db():
    with _session_scope() as db:
        yield db

# standalone function to be used outside of FastAPI
def get_db_standalone():
    return _session_scope()
