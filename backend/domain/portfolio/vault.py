from sqlalchemy.orm import Session
from backend.domain.portfolio.models import Trade, Portfolio, TradeStatus
from typing import List, Optional
import uuid

class TradeVault:
    def __init__(self, db: Session):
        self.db = db

    def create_portfolio(self, name: str, user_id: str) -> Portfolio:
        portfolio = Portfolio(name=name, user_id=user_id)
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def add_trade(self, trade_data: dict) -> Trade:
        trade = Trade(**trade_data)
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def close_trade(self, trade_id: uuid.UUID, exit_price: float, timestamp=None):
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        if trade:
            trade.status = TradeStatus.CLOSED
            # Append exit info to metadata
            meta = trade.meta_data or {}
            meta["exit_price"] = exit_price
            meta["exit_timestamp"] = str(timestamp)
            trade.meta_data = meta

            self.db.commit()
            self.db.refresh(trade)
        return trade

    def get_history(self, strategy_tag: Optional[str] = None) -> List[Trade]:
        query = self.db.query(Trade)
        if strategy_tag:
            query = query.filter(Trade.strategy_tag == strategy_tag)
        return query.all()

    def get_portfolio_trades(self, portfolio_id: uuid.UUID) -> List[Trade]:
        return self.db.query(Trade).filter(Trade.portfolio_id == portfolio_id).all()
