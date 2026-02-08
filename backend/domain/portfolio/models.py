from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SqEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime
from backend.domain.common.base import Base
import enum

class TradeSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)

    config = Column(JSONB, default={})  # Risk limits, allocation rules
    created_at = Column(DateTime, default=datetime.utcnow)

    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")

class Trade(Base):
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)
    ticker = Column(String, index=True)
    side = Column(SqEnum(TradeSide), nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    strategy_tag = Column(String, index=True)
    status = Column(SqEnum(TradeStatus), default=TradeStatus.OPEN)

    trade_group_id = Column(String, index=True, nullable=True)  # Links buy/sell legs
    meta_data = Column(JSONB, default={})  # For storing greeks, signals, etc at entry

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="trades")
