"""NSE Database Models - TimescaleDB Optimized"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, Text, Index, UniqueConstraint, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSONB
from backend.infrastructure.db import Base


class TimescaleMixin:
    """Mixin for TimescaleDB hypertable tables."""
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class HistoricalIndexData(Base, TimescaleMixin):
    """Historical Index OHLCV Data"""
    __tablename__ = "historical_index_data"

    id = Column(Integer, autoincrement=True, nullable=False)
    index_name = Column(String(100), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)

    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    total_traded_qty = Column(BigInteger)
    turnover_cr = Column(Float)
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    div_yield = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('trade_date', 'id'),
        UniqueConstraint('index_name', 'trade_date', name='uq_historical_index_data_unique'),
        Index('idx_historical_index_data_name_date', 'index_name', 'trade_date'),
    )


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


class IndexPERatio(Base, TimescaleMixin):
    """Index P/E Ratio"""
    __tablename__ = "index_pe_ratio"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(150), nullable=False, index=True)
    pe = Column(Float)
    pb = Column(Float)
    div_yield = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'symbol', name='uq_index_pe_ratio_unique'),
    )


class IndiaVIX(Base, TimescaleMixin):
    """India VIX"""
    __tablename__ = "india_vix"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    open_value = Column(Float)
    high_value = Column(Float)
    low_value = Column(Float)
    close_value = Column(Float)
    points_change = Column(Float)
    percent_change = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', name='uq_india_vix_date_unique'),
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
    change_in_oi = Column(BigInteger)
    total_trading_vol = Column(BigInteger)
    total_trf_val = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('trade_date', 'id'),
        UniqueConstraint('trade_date', 'ticker_symb', 'instrument_type', 'expiry_date', 'strike_price', 'option_type',
                        name='uq_bhavcopy_fo_unique'),
        Index('idx_bhavcopy_fo_symbol_expiry', 'ticker_symb', 'expiry_date'),
        Index('idx_bhavcopy_fo_date_symb', text('trade_date DESC'), text('ticker_symb ASC')),
    )


class FAOParticipantOI(Base, TimescaleMixin):
    """F&O Participant-wise OI"""
    __tablename__ = "fao_participant_oi"

    id = Column(Integer, autoincrement=True, nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    client_type = Column(String(20), nullable=False)

    future_index_long = Column(BigInteger, default=0)
    future_index_short = Column(BigInteger, default=0)
    future_stock_long = Column(BigInteger, default=0)
    future_stock_short = Column(BigInteger, default=0)
    option_index_call_long = Column(BigInteger, default=0)
    option_index_put_long = Column(BigInteger, default=0)
    option_index_call_short = Column(BigInteger, default=0)
    option_index_put_short = Column(BigInteger, default=0)
    option_stock_call_long = Column(BigInteger, default=0)
    option_stock_put_long = Column(BigInteger, default=0)
    option_stock_call_short = Column(BigInteger, default=0)
    option_stock_put_short = Column(BigInteger, default=0)
    total_long_contracts = Column(BigInteger, default=0)
    total_short_contracts = Column(BigInteger, default=0)

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


class SymbolMaster(Base):
    """Custom user-provided mapping for symbols, indices, sectors, and liquidity tiers."""
    __tablename__ = "symbol_master"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    symbol = Column(String(50), nullable=False, unique=True, index=True) # e.g. HDFCBANK
    company_name = Column(String(255), nullable=True)                    # e.g. HDFC Bank
    broad_index = Column(String(100), nullable=True)                     # e.g. Nifty 50
    sector_index = Column(String(100), nullable=True)                    # e.g. Nifty Bank
    derivative_liquidity_tier = Column(String(50), nullable=True)        # e.g. Tier 1
    typical_hedge_index = Column(String(50), nullable=True)              # e.g. BANKNIFTY

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


class ExchangeCircular(Base, TimescaleMixin):
    """Stores Exchange Circulars metadata (does not store actual PDF blob)"""
    __tablename__ = "exchange_circulars"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    trade_date = Column(Date, nullable=False, index=True) # Mapped to circular date
    circular_no = Column(String(100), nullable=False, unique=True, index=True)
    subject = Column(String(1000), nullable=True)
    department = Column(String(100), nullable=True)
    link = Column(String(500), nullable=True)

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
    parsed_dividend_amount = Column(Float)
    dividend_type = Column(String(50))
    broadcast_date = Column(DateTime)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'symbol', 'purpose', name='uq_corp_action_unique'),
    )

class BoardMeeting(Base, TimescaleMixin):
    """Board Meetings for Equities"""
    __tablename__ = "board_meetings"

    id = Column(Integer, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False, index=True) # Renamed from bm_date for Timescale consistency
    meeting_date = Column(Date, nullable=True) # Actual meeting date
    symbol = Column(String(50), nullable=False, index=True)
    company_name = Column(String(200))
    purpose = Column(Text)
    bm_desc = Column(Text)
    broadcast_date = Column(DateTime)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'id'),
        UniqueConstraint('date', 'symbol', 'purpose', name='uq_board_meeting_unique'),
    )


class DailyDerivativesAnalysis(Base, TimescaleMixin):
    """Composite Daily Derivatives Analysis"""
    __tablename__ = "daily_derivatives_analysis"

    id = Column(Integer, autoincrement=True, nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)

    # Core Price & OI Metrics
    close_price = Column(Float)            # Near Month Futures Close
    futures_total_vol = Column(BigInteger) # Sum of Vol across all futures expiries
    futures_total_oi = Column(BigInteger)  # Sum of OI across all futures expiries
    pcr_oi = Column(Float)                 # Total Put OI / Total Call OI
    highest_oi_strike_pe = Column(Float)   # Highest concentration OI strike price for PE
    highest_oi_strike_ce = Column(Float)   # Highest concentration OI strike price for CE
    highest_oi_pe_value = Column(Float)
    highest_oi_ce_value = Column(Float)
    highest_oi_pe_oi = Column(BigInteger)
    highest_oi_ce_oi = Column(BigInteger)
    pct_away_highest_pe = Column(Float)    # % Away (Highest PE Strike from Cash Close)
    pct_away_highest_ce = Column(Float)    # % Away (Highest CE Strike from Cash Close)
    chg_oi_options = Column(BigInteger)    # Total change in OI options
    chg_oi_futures = Column(BigInteger)    # Total change in OI futures
    near_expiry_date = Column(Date)        # Near Month Futures Expiry
    next_expiry_date = Column(Date)        # Next Month Futures Expiry
    far_expiry_date = Column(Date)         # Far Month Futures Expiry
    total_options_call_oi = Column(BigInteger) # Total Futures Calls OI
    total_options_put_oi = Column(BigInteger)  # Total Futures Puts OI

    # Volatility & Skew
    atm_iv_near = Column(Float)            # Near Month ATM IV
    atm_iv_next = Column(Float)            # Next Month ATM IV
    iv_rank_252 = Column(Float)            # IV Rank (252-day)
    iv_percentile_252 = Column(Float)      # IV Percentile (252-day)
    skew_25d_near = Column(Float)          # Near Month (Put 25d IV - Call 25d IV)
    skew_25d_far = Column(Float)           # Far Month (Put 25d IV - Call 25d IV)
    daily_volatility = Column(Float)       # 1 Sigma Daily Volatility (from fo_volatility)

    # Limits & Carry
    rollover_pct = Column(Float)           # (Next OI + Far OI) / Total OI
    mwpl_array = Column(JSONB)             # Array of top clients [{"client_1": 45.2}, ...]
    basis_1_bps = Column(Float)            # (Near Fut - Cash) / Cash * 10000
    basis_2_bps = Column(Float)            # (Next Fut - Cash) / Cash * 10000
    calendar_spread_1_bps = Column(Float)  # (Next Fut - Near Fut) / Near Fut * 10000
    calendar_spread_2_bps = Column(Float)  # (Far Fut - Next Fut) / Next Fut * 10000

    # Statistical & Valuation
    pe_ratio = Column(Float)               # Directly from pe_ratio table
    beta_252 = Column(Float)               # 252-day Log Return regression (Cash vs NIFTY)
    beta_500 = Column(Float)               # 500-day Log Return regression
    r_squared_252 = Column(Float)          # R-squared of 252-day regression
    r_squared_500 = Column(Float)          # R-squared of 500-day regression
    price_pct_change = Column(Float)       # 1-Day Price % Change
    relative_volume_20d = Column(Float)    # Relative Volume (20d SMA)

    # Cash Technicals
    atr_14_cash = Column(Float)            # 14-day SMA of True Range (Cash)
    ema_20_cash = Column(Float)            # 20-day EMA (Cash Close)
    ema_50_cash = Column(Float)            # 50-day EMA (Cash Close)
    ema_100_cash = Column(Float)           # 100-day EMA (Cash Close)
    vwap = Column(Float)                   # VWAP
    ema_200_cash = Column(Float)           # 200-day EMA (Cash Close)

    # Cash Delivery (from mto)
    mavg_delivery_vol_pct_5d = Column(Float)  # 5-day Avg Delivery %
    mavg_delivery_vol_pct_10d = Column(Float) # 10-day Avg Delivery %
    mavg_delivery_vol_pct_20d = Column(Float) # 20-day Avg Delivery %
    mavg_delivery_vol_pct_30d = Column(Float) # 30-day Avg Delivery %

    __table_args__ = (
        PrimaryKeyConstraint('trade_date', 'id'),
        UniqueConstraint('trade_date', 'symbol', name='uq_daily_deriv_analysis_unique'),
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

class AIPrediction(Base):
    """AI Prediction Logs for Benchmarking"""
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), index=True)
    ticker = Column(String(50), index=True)
    engine_type = Column(String(50))
    predicted_price = Column(Float)
    actual_price = Column(Float, nullable=True) # Updated later by background worker
    action = Column(String(50))
    target = Column(Float)
    stop_loss = Column(Float)
    confidence = Column(Integer)
    rationale = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FIIDIICash(Base, TimescaleMixin):
    """FII/DII Cash Market Activity"""
    __tablename__ = "fii_dii_cash"

    id = Column(Integer, autoincrement=True, nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    category = Column(String(50), nullable=False) # e.g., 'FII', 'DII'
    buy_value = Column(Float, nullable=True) # in Crores usually
    sell_value = Column(Float, nullable=True) # in Crores usually
    net_value = Column(Float, nullable=True) # in Crores usually

    __table_args__ = (
        PrimaryKeyConstraint('id', 'trade_date'),
        Index('idx_fii_dii_cash_date', 'trade_date'),
        UniqueConstraint('trade_date', 'category', name='uq_fii_dii_cash_unique')
    )
