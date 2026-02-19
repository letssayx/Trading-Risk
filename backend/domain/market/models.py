"""
Database models for market data
"""
from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint, Index
from backend.infrastructure.db import Base
from datetime import datetime

class Bhavcopy(Base):
    """
    NSE Bhavcopy data in UDIFF format - supports both CM and FO segments
    """
    __tablename__ = 'bhavcopy'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core identifiers
    trade_date = Column(Date, nullable=False, index=True)
    segment = Column(String(2), nullable=False, index=True)  # CM or FO
    instrument_type = Column(String(10), nullable=False)  # STK, FUTSTK, OPTSTK, FUTIDX, OPTIDX
    symbol = Column(String(20), nullable=False, index=True)

    # CM specific fields
    series = Column(String(10))  # EQ, BE for CM; NULL for FO
    isin = Column(String(12))

    # FO specific fields
    expiry_date = Column(Date, index=True)  # XpryDt
    strike_price = Column(Float)  # StrkPric
    option_type = Column(String(3))  # OptnTp: CE, PE, XX for futures
    underlying = Column(String(20))  # Underlying asset for derivatives

    # Price fields
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    last = Column(Float)
    prev_close = Column(Float)
    settlement_price = Column(Float)  # SttlmPric for FO

    # Volume & OI fields
    total_traded_qty = Column(Integer)
    total_traded_val = Column(Float)
    total_trades = Column(Integer)
    open_interest = Column(Integer)  # OpnIntrst for FO
    change_in_oi = Column(Integer)   # ChngInOpnIntrst

    # Metadata
    created_at = Column(Date, nullable=False, default=datetime.now)
    updated_at = Column(Date, default=datetime.now, onupdate=datetime.now)

    # Ensure uniqueness using Partial Indexes to handle NULLs correctly
    __table_args__ = (
        # CM Unique Index
        Index('ix_bhavcopy_cm_unique',
            'symbol', 'trade_date', 'series',
            unique=True,
            postgresql_where=(segment == 'CM')),

        # FO Unique Index
        Index('ix_bhavcopy_fo_unique',
            'symbol', 'trade_date', 'expiry_date', 'strike_price', 'option_type',
            unique=True,
            postgresql_where=(segment == 'FO')),
    )


class ImportHistory(Base):
    """
    Track which files/dates have been imported
    """
    __tablename__ = 'import_history'

    id = Column(Integer, primary_key=True)
    file_name = Column(String, nullable=False)
    file_date = Column(Date, nullable=False)
    segment = Column(String(50))  # CM, FO, or BOTH
    rows_imported = Column(Integer)
    import_date = Column(Date, nullable=False)
    checksum = Column(String(64))  # To detect if file changed

    __table_args__ = (
        UniqueConstraint('file_name', 'file_date', name='unique_import'),
    )
