# models.py
import uuid
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.sysutcdatetime(), nullable=False)
