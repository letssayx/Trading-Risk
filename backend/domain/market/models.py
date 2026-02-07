from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Instrument(Base):
    """Universal registry for symbols across NSE, CBOT, etc."""
    __tablename__ = 'instruments'

    turtle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), nullable=False)
    name = Column(Text)
    exchange = Column(String(10), nullable=False) # NSE, CBOT, etc.
    asset_class = Column(String(20)) # Equity, Option, Future
    vendor_key = Column(String(50), unique=True) # Upstox instrument_key
    lot_size = Column(Integer, default=1)

    # GIN Index for Fuzzy Search (pg_trgm)
    __table_args__ = (
        Index('idx_instrument_ticker_trgm', ticker, postgresql_using='gin', postgresql_ops={'ticker': 'gin_trgm_ops'}),
    )

class MarketData(Base):
    """TimescaleDB Hypertable for time-series price and Greek data."""
    __tablename__ = 'market_data'

    time = Column(DateTime(timezone=True), primary_key=True)
    turtle_id = Column(UUID(as_uuid=True), ForeignKey('instruments.turtle_id'), primary_key=True)
    open = Column(Numeric)
    high = Column(Numeric)
    low = Column(Numeric)
    close = Column(Numeric)
    volume = Column(Integer)
    iv = Column(Numeric) # Implied Volatility
    greeks = Column(JSONB) # {delta: 0.5, gamma: 0.001, ...}

    # Ensure no duplicates for same instrument at same time
    # Note: TimescaleDB handles PK constraint on time+turtle_id naturally if defined as PK.
    # We already have (time, turtle_id) as primary_key=True in definitions.

class CashDelivery(Base):
    """
    NSE Delivery Data (MTO).
    """
    __tablename__ = 'cash_delivery'

    date = Column(DateTime, primary_key=True)
    symbol = Column(String(20), primary_key=True)
    traded_qty = Column(Integer)
    delivery_qty = Column(Integer)
    delivery_pct = Column(Numeric)

class LargeDeal(Base):
    """
    Bulk and Block Deals.
    """
    __tablename__ = 'large_deals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime)
    symbol = Column(String(20))
    client_name = Column(String)
    deal_type = Column(String) # 'BULK', 'BLOCK'
    buy_sell = Column(String(4)) # 'BUY', 'SELL'
    quantity = Column(Integer)
    price = Column(Numeric)
