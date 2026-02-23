from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from backend.infrastructure.db import Base

class SystemLog(Base):
    """
    Centralized System Log / Audit Trail
    Optimized for heavy write/read with TimescaleDB (if available) or standard Postgres partitioning.
    """
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    level = Column(String(20), index=True)   # INFO, ERROR, WARNING, USER_ACTION
    source = Column(String(50), index=True)  # Backend, Frontend, Celery, Importer
    event_type = Column(String(50))          # Click, API_Call, DB_Query, System_Event

    message = Column(Text)
    user_id = Column(String(50), nullable=True) # If we have auth later
    meta_data = Column(JSONB, nullable=True)     # Extra context (latency, affected_rows, etc)

    # Indexes for fast filtering
    __table_args__ = (
        Index('idx_syslog_ts_level', 'timestamp', 'level'),
        Index('idx_syslog_source', 'source'),
    )
