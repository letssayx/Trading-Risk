from sqlalchemy import Column, String, Integer, DateTime, Text, func, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.domain.market.models import Base
import uuid

class Strategy(Base):
    """Stores the Python logic and AI-derived configurations."""
    __tablename__ = 'strategies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True) # Changed to String to match AuditTrail and generic User
    name = Column(String(100))
    type = Column(String(50), default="STRATEGY") # 'STRATEGY', 'RISK_MODEL'
    is_active = Column(Boolean, default=False)
    config_json = Column(JSONB) # The natural language parameters
    source_code = Column(Text)  # The actual Python script for the Brain
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
