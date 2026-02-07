from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from backend.domain.market.models import Base

# Assuming 'trades' table exists or creating a new model for it here if not in domain/market/models
# For core logic, we will define a TradeRecord model here or import.
# Checking backend/domain/risk/models.py or similar might be good, but let's define a dedicated one for the Logger if missing.

class TradeRecord(Base):
    __tablename__ = 'trade_records'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(String, nullable=False)
    strategy_version = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    pnl = Column(Float, nullable=True)
    status = Column(String, default="OPEN") # OPEN, CLOSED

class TradeLogger:
    """
    Records Entry/Exit and tracks PnL.
    """
    def __init__(self, db: Session):
        self.db = db

    def log_entry(self, strategy_id: str, version: int, symbol: str, price: float, qty: int) -> str:
        trade = TradeRecord(
            strategy_id=strategy_id,
            strategy_version=version,
            symbol=symbol,
            entry_price=price,
            quantity=qty,
            status="OPEN"
        )
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return str(trade.id)

    def log_exit(self, trade_id: str, price: float):
        trade = self.db.query(TradeRecord).filter(TradeRecord.id == trade_id).first()
        if not trade: return False

        trade.exit_price = price
        trade.exit_time = datetime.utcnow()
        trade.status = "CLOSED"
        trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity

        self.db.commit()
        return True

    def calculate_open_pnl(self, current_prices: dict) -> float:
        """
        Calculates unrealized PnL for all OPEN trades.
        current_prices: { 'SYMBOL': price }
        """
        open_trades = self.db.query(TradeRecord).filter(TradeRecord.status == "OPEN").all()
        total_pnl = 0.0

        for trade in open_trades:
            curr_price = current_prices.get(trade.symbol)
            if curr_price:
                total_pnl += (curr_price - trade.entry_price) * trade.quantity

        return total_pnl
