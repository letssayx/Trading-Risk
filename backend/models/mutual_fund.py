from sqlalchemy import Column, String, Float, DateTime, Integer, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid
from backend.domain.common.base import Base

class MutualFundHolding(Base):
    __tablename__ = "mutual_fund_holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_date = Column(Date, index=True, nullable=False)
    fund_house = Column(String, index=True, nullable=False)
    scheme_name = Column(String, index=True, nullable=False)

    # Category of the holding: stock, fo, debt, debt_derivative
    asset_category = Column(String, index=True, nullable=False)

    symbol = Column(String, index=True, nullable=True)
    isin = Column(String, index=True, nullable=True)
    instrument_name = Column(String, nullable=True)

    # Common fields
    quantity = Column(Float, nullable=True)
    market_value = Column(Float, nullable=True)
    percent_to_nav = Column(Float, nullable=True)

    # F&O specific fields
    position = Column(String, nullable=True) # e.g. Long / Short
    strike_price = Column(Float, nullable=True)
    option_type = Column(String, nullable=True) # e.g. CALL / PUT

    # Debt / Debt Derivative specific fields
    maturity_date = Column(Date, nullable=True)
    yield_pct = Column(Float, nullable=True)
    coupon_pct = Column(Float, nullable=True)
    benchmark = Column(String, nullable=True) # e.g. Overnight MIBOR
    notional_amount = Column(Float, nullable=True)
