from sqlalchemy import Column, String, Integer, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
import uuid

# Base is typically shared, assuming it's imported or defined here.
# For modularity, we re-declare or import. Best practice is common Base.
# I will define Base locally for now or reuse if I refactor later.
Base = declarative_base()

class Strategy(Base):
    """Stores the Python logic and AI-derived configurations."""
    __tablename__ = 'strategies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    name = Column(String(100))
    config_json = Column(JSONB) # The natural language parameters
    source_code = Column(Text)  # The actual Python script for the Brain
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
