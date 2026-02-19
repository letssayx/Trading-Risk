from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from backend.domain.market.contract_manager import ContractManager
from backend.analysis.toolbox.price_oi import PriceOiAnalyzer
from backend.plugins.strategies.rollover import RolloverAnalyzer
import random
from datetime import datetime, timedelta

router = APIRouter()

# Mock Helper since we don't have real data source connected yet
def get_mock_contract_data(symbol: str, expiry_date=None):
    base_price = 1000 + random.random() * 500
    price = base_price * (1 + random.random() * 0.05)
    oi = int(100000 + random.random() * 500000)

    return {
        "symbol": symbol,
        "expiry": str(expiry_date) if expiry_date else "N/A",
        "close": round(price, 2),
        "open_interest": oi,
        "time": datetime.now().strftime("%Y-%m-%d")
    }

def get_mock_history(symbol: str, days=20):
    data = []
    base_price = 1000
    oi = 500000
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=days-i)
        if date.weekday() >= 5: continue

        price_change = (random.random() - 0.5) * 20
        base_price += price_change

        oi_change = (random.random() - 0.5) * 10000
        oi += int(oi_change)

        data.append({
            "time": date.strftime("%Y-%m-%d"),
            "close": round(base_price, 2),
            "open_interest": max(0, oi)
        })
    return data

@router.get("/api/analysis/oi/{symbol}")
async def analyze_oi(symbol: str):
    """
    Get Price vs OI Analysis for a symbol (usually the near month future).
    """
    # 1. Get Near Month Future Symbol
    futures = ContractManager.get_futures_symbols(symbol.upper())
    if not futures:
        raise HTTPException(status_code=404, detail="Symbol not found or no futures available")

    near_month = futures[0]

    # 2. Get Historical Data (Mock for now)
    history = get_mock_history(near_month)

    # 3. Analyze
    result = PriceOiAnalyzer.analyze_symbol(near_month, history)
    return result

@router.get("/api/analysis/rollover/{symbol}")
async def analyze_rollover(symbol: str):
    """
    Get Rollover Analysis between Near and Next month futures.
    """
    futures = ContractManager.get_futures_symbols(symbol.upper())
    if len(futures) < 2:
        raise HTTPException(status_code=404, detail="Not enough future contracts found")

    near_sym = futures[0]
    next_sym = futures[1]
    expiries = ContractManager.get_expiry_dates()

    # Mock Data Fetch
    near_data = get_mock_contract_data(near_sym, expiries[0])
    next_data = get_mock_contract_data(next_sym, expiries[1])

    # Analyze
    result = RolloverAnalyzer.analyze(symbol, near_data, next_data)
    return result
