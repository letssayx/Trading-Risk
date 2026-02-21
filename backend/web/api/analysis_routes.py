from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime, date

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy
from backend.analysis.toolbox.price_oi import PriceOiAnalyzer
from backend.plugins.strategies.rollover import RolloverAnalyzer

router = APIRouter()

def get_latest_data(db: Session, symbol: str, expiry: date):
    """
    Get the latest record for a specific future contract.
    """
    return db.query(Bhavcopy).filter(
        Bhavcopy.symbol == symbol,
        Bhavcopy.segment == 'FO',
        Bhavcopy.instrument_type.in_(['FUTSTK', 'FUTIDX']),
        Bhavcopy.expiry_date == expiry
    ).order_by(Bhavcopy.trade_date.desc()).first()

def get_history(db: Session, symbol: str, expiry: date, limit: int = 20):
    """
    Get history for a specific future contract.
    """
    results = db.query(Bhavcopy).filter(
        Bhavcopy.symbol == symbol,
        Bhavcopy.segment == 'FO',
        Bhavcopy.instrument_type.in_(['FUTSTK', 'FUTIDX']),
        Bhavcopy.expiry_date == expiry
    ).order_by(Bhavcopy.trade_date.asc()).all() # Oldest first for analysis

    # Return list of dicts
    data = []
    for row in results:
        data.append({
            "time": row.trade_date.strftime("%Y-%m-%d"),
            "close": row.close,
            "open_interest": row.open_interest or 0
        })
    return data

@router.get("/api/analysis/oi/{symbol}")
async def analyze_oi(symbol: str, db: Session = Depends(get_db)):
    """
    Get Price vs OI Analysis for a symbol (Underlying).
    Finds the Near Month Future and analyzes it.
    """
    symbol = symbol.upper()
    today = datetime.now().date()

    # 1. Find Near Month Expiry
    # Get all future expiries for this symbol >= today
    near_expiry_row = db.query(Bhavcopy.expiry_date).filter(
        Bhavcopy.symbol == symbol,
        Bhavcopy.segment == 'FO',
        Bhavcopy.instrument_type.in_(['FUTSTK', 'FUTIDX']),
        Bhavcopy.expiry_date >= today
    ).order_by(Bhavcopy.expiry_date.asc()).first()

    if not near_expiry_row:
        # Fallback: Maybe user passed a contract name?
        # But for now assume underlying.
        raise HTTPException(status_code=404, detail="No active futures found for symbol")

    near_expiry = near_expiry_row[0]

    # 2. Get Historical Data for this contract
    history = get_history(db, symbol, near_expiry, limit=30)

    if not history:
        raise HTTPException(status_code=404, detail="No data found for near month contract")

    # 3. Analyze
    # Pass a constructed "Contract Name" like RELIANCE-2024-02-29
    contract_name = f"{symbol} ({near_expiry})"
    result = PriceOiAnalyzer.analyze_symbol(contract_name, history)
    return result

@router.get("/api/analysis/rollover/{symbol}")
async def analyze_rollover(symbol: str, db: Session = Depends(get_db)):
    """
    Get Rollover Analysis between Near and Next month futures.
    """
    symbol = symbol.upper()
    today = datetime.now().date()

    # 1. Find Expiries
    expiries_rows = db.query(Bhavcopy.expiry_date).filter(
        Bhavcopy.symbol == symbol,
        Bhavcopy.segment == 'FO',
        Bhavcopy.instrument_type.in_(['FUTSTK', 'FUTIDX']),
        Bhavcopy.expiry_date >= today
    ).distinct().order_by(Bhavcopy.expiry_date.asc()).limit(2).all()

    if len(expiries_rows) < 2:
        raise HTTPException(status_code=404, detail="Not enough future contracts found (need Near & Next)")

    near_expiry = expiries_rows[0][0]
    next_expiry = expiries_rows[1][0]

    # 2. Get Latest Data for both
    near_data_row = get_latest_data(db, symbol, near_expiry)
    next_data_row = get_latest_data(db, symbol, next_expiry)

    if not near_data_row or not next_data_row:
        raise HTTPException(status_code=404, detail="Data missing for contracts")

    # Format for Analyzer
    near_data = {
        "symbol": symbol,
        "expiry": str(near_expiry),
        "close": near_data_row.close,
        "open_interest": near_data_row.open_interest or 0
    }

    next_data = {
        "symbol": symbol,
        "expiry": str(next_expiry),
        "close": next_data_row.close,
        "open_interest": next_data_row.open_interest or 0
    }

    # 3. Analyze
    result = RolloverAnalyzer.analyze(symbol, near_data, next_data)
    return result
