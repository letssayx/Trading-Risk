from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from backend.infrastructure.db import get_db
from backend.domain.market.service import MarketDataService
from backend.domain.market.contract_manager import ContractManager
from backend.analysis.toolbox.price_oi import PriceOiAnalyzer
from backend.plugins.strategies.rollover import RolloverAnalyzer

router = APIRouter()

@router.get("/api/analysis/oi/{symbol}")
async def analyze_oi(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get Price vs OI Analysis for a symbol.
    If 'symbol' is underlying (e.g. NIFTY), finds Near Month Future.
    """
    contract_symbol = symbol.upper()

    # Check if it's a contract or underlying
    parsed = ContractManager.parse_contract_symbol(contract_symbol)

    if not parsed:
        # It's an underlying. Find Near Month Future.
        contracts = MarketDataService.get_contracts_for_underlying(db, contract_symbol)
        if not contracts:
            raise HTTPException(status_code=404, detail="No futures contracts found for symbol")
        contract_symbol = contracts[0] # Assume sorted by expiry, so first is Near

    # Get Historical Data
    history = MarketDataService.get_daily_ohlc(db, contract_symbol, days=50, segment='FO')

    if not history:
        raise HTTPException(status_code=404, detail="No historical data found")

    # Analyze
    # PriceOiAnalyzer expects list of dicts with 'close', 'open_interest', 'time'
    # Our service returns 'oi' instead of 'open_interest' in the dict key?
    # Let's check service: "oi": row.open_interest or 0
    # Let's check PriceOiAnalyzer.analyze_symbol (memory says it's in backend/analysis/toolbox/price_oi.py)
    # I should map keys if needed.

    mapped_history = []
    for h in history:
        mapped_history.append({
            "time": h["time"],
            "close": h["close"],
            "open_interest": h["oi"]
        })

    result = PriceOiAnalyzer.analyze_symbol(contract_symbol, mapped_history)
    return result

@router.get("/api/analysis/rollover/{symbol}")
async def analyze_rollover(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get Rollover Analysis between Near and Next month futures.
    Symbol should be the Underlying (e.g. NIFTY).
    """
    contracts = MarketDataService.get_contracts_for_underlying(db, symbol.upper())

    if len(contracts) < 2:
        raise HTTPException(status_code=404, detail="Not enough future contracts found for rollover analysis")

    near_sym = contracts[0]
    next_sym = contracts[1]

    # Fetch latest data for both
    # We need just the latest record. get_daily_ohlc(days=1)
    near_data_list = MarketDataService.get_daily_ohlc(db, near_sym, days=1, segment='FO')
    next_data_list = MarketDataService.get_daily_ohlc(db, next_sym, days=1, segment='FO')

    if not near_data_list or not next_data_list:
         raise HTTPException(status_code=404, detail="Data missing for contracts")

    near_rec = near_data_list[0]
    next_rec = next_data_list[0]

    # Format for RolloverAnalyzer
    # Needs: symbol, expiry, close, open_interest, time
    near_data = {
        "symbol": near_rec["symbol"],
        "expiry": near_rec["expiry"],
        "close": near_rec["close"],
        "open_interest": near_rec["oi"],
        "time": near_rec["time"]
    }

    next_data = {
        "symbol": next_rec["symbol"],
        "expiry": next_rec["expiry"],
        "close": next_rec["close"],
        "open_interest": next_rec["oi"],
        "time": next_rec["time"]
    }

    # Analyze
    result = RolloverAnalyzer.analyze(symbol, near_data, next_data)
    return result
