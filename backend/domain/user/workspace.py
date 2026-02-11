from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid
from datetime import datetime
from backend.domain.common.base import Base

class Workspace(Base):
    """
    Persists user workspace layout (window positions, active widgets).
    """
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False) # e.g. "Morning Setup"

    # Layout Config: {"layout": [{"i": "chart", "x": 0, "y": 0, "w": 6, "h": 4}], "theme": "dark"}
    layout_config = Column(JSONB, default={})

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
