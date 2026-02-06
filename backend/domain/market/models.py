from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class InstrumentModel(Base):
    __tablename__ = 'instruments'

    turtle_id = Column(String, primary_key=True)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    exchange_token = Column(String) # Exchange specific key
    instrument_type = Column(String) # Future, Option, Equity, Commodity, Index
    asset_class = Column(String) # Equity, Commodity, FX, Crypto
    details = Column(JSON) # Contract size, expiry, tick_size, lot_size

class MarketData(Base):
    __tablename__ = 'market_data'

    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    open_interest = Column(Float)

    # Greeks (if applicable)
    delta = Column(Float)
    gamma = Column(Float)
    vega = Column(Float)
    theta = Column(Float)

    # TimescaleDB Hypertable primary key composite
    __table_args__ = (
        PrimaryKeyConstraint('timestamp', 'symbol'),
    )
