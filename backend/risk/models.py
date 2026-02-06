from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Trade(Base):
    """Registry for manual or API-synced trades."""
    __tablename__ = 'trades'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trader_id = Column(UUID(as_uuid=True), index=True)
    desk_id = Column(UUID(as_uuid=True), index=True)
    # turtle_id linked to instruments.turtle_id, but we mock the FK relationship for now or assume schema
    turtle_id = Column(UUID(as_uuid=True))
    side = Column(String(10)) # BUY/SELL
    quantity = Column(Integer)
    entry_price = Column(Numeric)
    status = Column(String(20)) # ACTIVE, CLOSED

class RiskSnapshot(Base):
    """Stores the results of the 'Red Box' stress tests."""
    __tablename__ = 'risk_snapshots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True)) # trader_id or desk_id
    timestamp = Column(DateTime(timezone=True))
    worst_case_pnl = Column(Numeric) # Result of the -10% shock scenario
    net_delta = Column(Numeric)
    net_gamma = Column(Numeric)
