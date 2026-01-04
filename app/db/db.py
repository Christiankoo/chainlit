# db.py
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import SERVER, DATABASE, USERNAME, PASSWORD

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
