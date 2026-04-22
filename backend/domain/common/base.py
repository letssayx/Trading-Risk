from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid
from datetime import datetime

Base = declarative_base()

class UserOverride(Base):
    """
    Sovereign Object: Stores user-specific overrides for default strategies.
    Ensures the 'Default Layer' remains immutable.
    """
    __tablename__ = "user_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True, nullable=False)
    strategy_name = Column(String, index=True, nullable=False)

    # The override parameters (e.g. {"N_Multiplier": 2.5, "Risk_Pct": 0.02})
    override_config = Column(JSONB, nullable=False)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
