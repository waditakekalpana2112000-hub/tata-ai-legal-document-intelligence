from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from backend.database import Base


class QueryLog(Base):
    """Every question asked + the AI's answer (audit trail)."""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    task = Column(String, index=True)
    source = Column(String, nullable=True)
    question = Column(Text)
    answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
