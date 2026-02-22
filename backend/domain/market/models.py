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

    # Core identifiers (TradDt, Sgmt, FinInstrmTp, TckrSymb)
    trade_date = Column(Date, nullable=False, index=True) # TradDt
    segment = Column(String(2), nullable=False, index=True)  # Sgmt: CM or FO
    instrument_type = Column(String(10), nullable=False)  # FinInstrmTp
    symbol = Column(String(20), nullable=False, index=True) # TckrSymb

    # Additional Identification
    biz_date = Column(Date) # BizDt
    source = Column(String(10)) # Src
    fin_instrm_id = Column(String(20)) # FinInstrmId
    isin = Column(String(12)) # ISIN
    instrument_name = Column(String(50)) # FinInstrmNm
    session_id = Column(String(10)) # SsnId
    remarks = Column(String(50)) # Rmks

    # CM specific fields
    series = Column(String(10))  # SctySrs (EQ, BE, etc.)

    # FO specific fields
    expiry_date = Column(Date, index=True)  # XpryDt
    actual_expiry_date = Column(Date) # FininstrmActlXpryDt
    strike_price = Column(Float)  # StrkPric
    option_type = Column(String(3))  # OptnTp: CE, PE, XX
    underlying = Column(String(20))  # UndrlygPric is price, not symbol? Wait.
    # UDIFF 'UndrlygPric' is Underlying Price. 'Underlying' symbol is usually implied or separate.
    # In UDIFF, the underlying symbol isn't always explicit row-by-row if it's TckrSymb.
    # We will store 'underlying_price' instead if mapped.
    underlying_price = Column(Float) # UndrlygPric

    # Market Data
    open = Column(Float) # OpnPric
    high = Column(Float) # HghPric
    low = Column(Float) # LwPric
    close = Column(Float) # ClsPric
    last = Column(Float) # LastPric
    prev_close = Column(Float) # PrvsClsgPric
    settlement_price = Column(Float)  # SttlmPric

    # Volume & OI fields
    total_traded_qty = Column(Integer) # TtlTradgVol
    total_traded_val = Column(Float) # TtlTrfVal
    total_trades = Column(Integer) # TtlNbOfTxsExctd
    open_interest = Column(Integer)  # OpnIntrst
    change_in_oi = Column(Integer)   # ChngInOpnIntrst

    lot_size = Column(Integer) # NewBrdLotQty

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
