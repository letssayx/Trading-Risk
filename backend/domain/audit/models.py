from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from backend.domain.market.models import Base

class AuditTrail(Base):
    __tablename__ = "audit_trail"

    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False) # Simplification: String for now (or UUID if User model strict)
    action_type = Column(String, nullable=False) # 'TWEAK_PARAM', 'UPDATE_CODE', 'TOGGLE_PLUGIN'
    entity_type = Column(String, nullable=False) # 'STRATEGY', 'RISK_MODEL'
    entity_id = Column(String, nullable=True) # UUID of the strategy/model
    before_state = Column(JSONB, nullable=True)
    after_state = Column(JSONB, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "audit_id": str(self.audit_id),
            "user_id": self.user_id,
            "action_type": self.action_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "timestamp": self.timestamp.isoformat()
        }
