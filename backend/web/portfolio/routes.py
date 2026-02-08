from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.domain.portfolio.models import Portfolio, Trade, TradeStatus
from backend.domain.portfolio.schemas import PortfolioCreate, PortfolioResponse, TradeCreate, TradeResponse
from backend.domain.portfolio.vault import TradeVault
from backend.dependencies import get_db, get_current_user

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

@router.post("/", response_model=PortfolioResponse)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    db_portfolio = Portfolio(**portfolio.dict())
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

@router.get("/", response_model=List[PortfolioResponse])
def read_portfolios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    portfolios = db.query(Portfolio).offset(skip).limit(limit).all()
    return portfolios

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def read_portfolio(portfolio_id: UUID, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.post("/{portfolio_id}/trades/", response_model=TradeResponse)
def create_trade_for_portfolio(portfolio_id: UUID, trade: TradeCreate, db: Session = Depends(get_db)):
    db_trade = Trade(**trade.dict(), portfolio_id=portfolio_id)
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

@router.put("/trades/{trade_id}/close", response_model=TradeResponse)
def close_trade(trade_id: UUID, exit_price: float, db: Session = Depends(get_db)):
    vault = TradeVault(db)
    trade = vault.close_trade(trade_id, exit_price)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade
