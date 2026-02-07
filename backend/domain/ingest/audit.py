from sqlalchemy import Column, String, Integer, DateTime, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from backend.domain.market.models import Base

class IngestionAudit(Base):
    """
    Tracks processed files to prevent duplicates (Idempotency).
    """
    __tablename__ = "ingestion_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True) # SHA-256
    file_type = Column(String, nullable=False) # 'BHAVCOPY', 'DELIVERY', etc.
    status = Column(String, default="SUCCESS")
    record_count = Column(Integer, default=0)
    processed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('file_name', 'file_hash', name='uq_file_ingest'),
    )
