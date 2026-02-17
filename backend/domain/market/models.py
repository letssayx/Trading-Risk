from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint
from backend.infrastructure.db import Base

class Bhavcopy(Base):
    __tablename__ = 'bhavcopy'

    id = Column(Integer, primary_key=True, index=True)
    trade_date = Column(Date, index=True)  # TradDt
    business_date = Column(Date)  # BizDt
    segment = Column(String(2))  # Sgmt (CM/FO)
    instrument_type = Column(String(3))  # FinInstrmTp (STK/STF/etc)
    symbol = Column(String(20), index=True)  # TckrSymb
    series = Column(String(10))  # SctySrs (EQ/BE/etc)
    isin = Column(String(12))  # ISIN

    # Prices
    open = Column(Float)  # OpnPric
    high = Column(Float)  # HghPric
    low = Column(Float)  # LwPric
    close = Column(Float)  # ClsPric
    last = Column(Float)  # LastPric
    prev_close = Column(Float)  # PrvsClsgPric

    # Volume
    total_traded_qty = Column(Integer)  # TtlTradgVol
    total_traded_val = Column(Float)  # TtlTrfVal
    total_trades = Column(Integer)  # TtlNbOfTxsExctd

    # Composite unique constraint to prevent duplicates
    __table_args__ = (
        UniqueConstraint('symbol', 'trade_date', 'series', name='unique_symbol_date_series'),
    )
