from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from backend.domain.portfolio.models import Portfolio, Trade, TradeStatus
from backend.domain.portfolio.schemas import PortfolioCreate, PortfolioResponse, TradeCreate, TradeResponse
# from backend.domain.portfolio.vault import TradeVault # Assuming this exists or will be implemented
from backend.dependencies import get_db

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
    return db.query(Portfolio).offset(skip).limit(limit).all()

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def read_portfolio(portfolio_id: UUID, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.post("/{portfolio_id}/trades/", response_model=TradeResponse)
def create_trade_for_portfolio(portfolio_id: UUID, trade: TradeCreate, db: Session = Depends(get_db)):
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not db_portfolio:
         raise HTTPException(status_code=404, detail="Portfolio not found")

    db_trade = Trade(**trade.dict(), portfolio_id=portfolio_id)
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade
