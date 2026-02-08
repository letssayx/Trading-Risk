from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum

class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class TradeBase(BaseModel):
    ticker: str
    side: TradeSide
    qty: int
    price: float
    strategy_tag: Optional[str] = None
    trade_group_id: Optional[str] = None
    meta_data: Optional[Dict] = {}

class TradeCreate(TradeBase):
    portfolio_id: UUID

class TradeResponse(TradeBase):
    id: UUID
    status: TradeStatus
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PortfolioBase(BaseModel):
    name: str
    user_id: str
    config: Optional[Dict] = {}

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioResponse(PortfolioBase):
    id: UUID
    created_at: datetime
    trades: List[TradeResponse] = []

    class Config:
        orm_mode = True
