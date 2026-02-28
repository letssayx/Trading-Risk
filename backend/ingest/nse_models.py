"""NSE Database Models - TimescaleDB Optimized"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, Text, Index, UniqueConstraint, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from backend.infrastructure.db import Base


class TimescaleMixin:
    """Mixin for TimescaleDB hypertable tables."""
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class BhavcopyEQ(Base, TimescaleMixin):
    """Equity Bhavcopy - EQ series only"""
    __tablename__ = "bhavcopy_eq"

    id = Column(Integer, autoincrement=True, nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    series = Column(String(10), nullable=False)
    trade_date = Column(Date, nullable=False, index=True)

    prev_close = Column(Float)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    last_price = Column(Float)
    close_price = Column(Float)
    avg_price = Column(Float)
    total_traded_qty = Column(BigInteger)
    turnover_lacs = Column(Float)
    no_of_trades = Column(Integer)
    deliverable_qty = Column(BigInteger)
    deliverable_pct = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('trade_date', 'id'),
        UniqueConstraint('symbol', 'series', 'trade_date', name='uq_bhavcopy_eq_unique'),
        Index('idx_bhavcopy_eq_symbol_date', 'symbol', 'trade_date'),
    )


class BhavcopyFO(Base, TimescaleMixin):
    """F&O Bhavcopy"""
    __tablename__ = "bhavcopy_fo"

    id = Column(Integer, autoincrement=True, nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    ticker_symb = Column(String(50), nullable=False, index=True)
    instrument_type = Column(String(20), nullable=True, index=True)  # Added for FO visibility
    expiry_date = Column(Date, index=True)
    strike_price = Column(Float)
    option_type = Column(String(5))
    instrument_name = Column(String(100))

    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    settle_price = Column(Float)
    open_interest = Column(BigInteger)
    change_in_oi = Column(Integer)
    total_trading_vol = Column(BigInteger)
    total_trf_val = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('trade_date', 'id'),
        UniqueConstraint('trade_date', 'ticker_symb', 'expiry_date', 'strike_price', 'option_type',
                        name='uq_bhavcopy_fo_unique'),
        Index('idx_bhavcopy_fo_symbol_expiry', 'ticker_symb', 'expiry_date'),
    )


class FAOParticipantOI(Base, TimescaleMixin):
    """F&O Participant-wise OI"""
    __tablename__ = "fao_participant_oi"

    id = Column(Integer, autoincrement=True, nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    client_type = Column(String(20), nullable=False)

    future_index_long = Column(Integer, default=0)
    future_index_short = Column(Integer, default=0)
    future_stock_long = Column(Integer, default=0)
    future_stock_short = Column(Integer, default=0)
    option_index_call_long = Column(Integer, default=0)
    option_index_put_long = Column(Integer, default=0)
    option_index_call_short = Column(Integer, default=0)
    option_index_put_short = Column(Integer, default=0)
    option_stock_call_long = Column(Integer, default=0)
    option_stock_put_long = Column(Integer, default=0)
    option_stock_call_short = Column(Integer, default=0)
    option_stock_put_short = Column(Integer, default=0)
    total_long_contracts = Column(Integer, default=0)
    total_short_contracts = Column(Integer, default=0)

    __table_args__ = (
        PrimaryKeyConstraint('trade_date', 'id'),
        UniqueConstraint('trade_date', 'client_type', name='uq_fao_oi_unique'),
    )


class FOVolatility(Base, TimescaleMixin):
    """F&O Volatility"""
    __tablename__ = "fo_volatility"

    id = Column(Integer, autoincrement=True, nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)

    underlying_close_price = Column(Float)
    underlying_annualised_vol = Column(Float)
    futures_close_price = Column(Float)
    futures_annualised_vol = Column(Float)
    applicable_daily_vol = Column(Float)
    applicable_annualised_vol = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('trade_date', 'id'),
        UniqueConstraint('trade_date', 'symbol', name='uq_fo_volatility_unique'),
    )


class BlockDeal(Base, TimescaleMixin):
    """Block Deals"""
    __tablename__ = "block_deals"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    security_name = Column(String(200))
    client_name = Column(String(200))
    buy_sell = Column(String(10))
    quantity_traded = Column(BigInteger)
    trade_price = Column(Float)
    remarks = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        # Unique constraint removed to allow multiple trades per client/day
    )


class BulkDeal(Base, TimescaleMixin):
    """Bulk Deals"""
    __tablename__ = "bulk_deals"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    security_name = Column(String(200))
    client_name = Column(String(200))
    buy_sell = Column(String(10))
    quantity_traded = Column(BigInteger)
    trade_price = Column(Float)
    remarks = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        # Unique constraint removed to allow multiple trades per client/day
    )


class FIIDerivativesStat(Base, TimescaleMixin):
    """FII Derivatives Statistics"""
    __tablename__ = "fii_derivatives_stats"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    instrument_type = Column(String(50), nullable=False)

    buy_contracts = Column(Integer)
    buy_amt_crores = Column(Float)
    sell_contracts = Column(Integer)
    sell_amt_crores = Column(Float)
    oi_contracts = Column(Integer)
    oi_amt_crores = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'instrument_type', name='uq_fii_stats_unique'),
    )


class MTODelivery(Base, TimescaleMixin):
    """MTO Delivery Position"""
    __tablename__ = "mto_delivery"

    id = Column(Integer, autoincrement=True, nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    settlement_type = Column(String(10), default='N')
    sr_no = Column(BigInteger)
    security_name = Column(String(200), nullable=False)
    quantity_traded = Column(BigInteger)
    deliverable_qty = Column(BigInteger)
    deliverable_pct = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('trade_date', 'id'),
        UniqueConstraint('trade_date', 'security_name', name='uq_mto_delivery_unique'),
    )


class MWPLClientPosition(Base, TimescaleMixin):
    """MWPL Client Position"""
    __tablename__ = "mwpl_client_position"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    underlying_stock = Column(String(50), nullable=False, index=True)
    client_position_num = Column(Integer, nullable=False)
    position_pct = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'underlying_stock', 'client_position_num', name='uq_mwpl_unique'),
    )


class SecurityMaster(Base):
    """Security Master (NOT time-series - no hypertable)"""
    __tablename__ = "security_master"

    fin_instrm_id = Column(String(50), primary_key=True)
    ticker_symb = Column(String(50), nullable=False, index=True)
    security_series = Column(String(10))
    instrument_name = Column(String(200))
    isin = Column(String(20), unique=True, index=True)
    new_brd_lot_qty = Column(Integer)
    par_val = Column(Float)
    issued_capital = Column(Float)
    listed_date = Column(Date)
    additional_info = Column(Text)
    special_ex_date = Column(Date)
    status = Column(String(20))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PERatio(Base, TimescaleMixin):
    """P/E Ratio"""
    __tablename__ = "pe_ratio"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(150), nullable=False, index=True)
    symbol_pe = Column(Float)
    adjusted_pe = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'symbol', name='uq_pe_ratio_unique'),
    )


class VaRStat(Base, TimescaleMixin):
    """VaR Statistics (Begin/End of Day)"""
    __tablename__ = "var_stats"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    series = Column(String(10))
    security_var = Column(Float)
    index_var = Column(Float)
    var_margin = Column(Float)
    extreme_loss_rate = Column(Float)
    adho_margin = Column(Float)
    applicable_margin_rate = Column(Float)
    file_type = Column(String(10)) # BEGIN or END

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'symbol', 'series', 'file_type', name='uq_var_stats_unique'),
    )


class ContractDelta(Base, TimescaleMixin):
    """NCL Contract Delta"""
    __tablename__ = "contract_delta"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    expiry_date = Column(Date)
    strike_price = Column(Float)
    option_type = Column(String(5))
    delta = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'symbol', 'expiry_date', 'strike_price', 'option_type', name='uq_contract_delta_unique'),
    )


class Auction(Base, TimescaleMixin):
    """Securities for Auction"""
    __tablename__ = "auctions"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    series = Column(String(10))
    auction_qty = Column(Integer)
    best_buy_price = Column(Float)
    best_sell_price = Column(Float)
    auction_price = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'symbol', 'series', name='uq_auctions_unique'),
    )


class MarginTrading(Base, TimescaleMixin):
    """Margin Trading Disclosure"""
    __tablename__ = "margin_trading"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    quantity_funded = Column(Integer)
    amount_funded = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'symbol', name='uq_margin_trading_unique'),
    )


class CorporateAction(Base, TimescaleMixin):
    """Corporate Actions for Equities"""
    __tablename__ = "corporate_actions"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True) # Renamed from ex_date for Timescale consistency
    symbol = Column(String(50), nullable=False, index=True)
    company_name = Column(String(200))
    series = Column(String(20))
    face_value = Column(Float)
    purpose = Column(Text)
    ex_date = Column(Date) # Explicitly keep original if different from import date
    record_date = Column(Date)
    bc_start_date = Column(Date)
    bc_end_date = Column(Date)
    nd_start_date = Column(Date)
    nd_end_date = Column(Date)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'symbol', 'purpose', name='uq_corp_action_unique'),
    )


class ImportLog(Base):
    """Import Audit Log"""
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True)
    import_date = Column(Date, index=True)
    table_name = Column(String(50), index=True)
    status = Column(String(20))
    rows_inserted = Column(Integer)
    rows_updated = Column(Integer, default=0)
    error_msg = Column(Text)
    source_file = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
