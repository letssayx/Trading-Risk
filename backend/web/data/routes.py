from fastapi import APIRouter, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import pandas as pd

# In prod, this would import from backend.data.loader
# from backend.data.loader import NSEDataLoader

router = APIRouter(prefix="/api", tags=["Market Data"])

@router.get("/historical/{symbol}")
async def get_historical_data(symbol: str, years: int = 5):
    """
    Returns mock OHLCV data for charts.
    """
    # Generate 5 years of daily data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)

    dates = pd.date_range(start=start_date, end=end_date, freq='B') # Business days
    price = 100.0
    data = []

    for date in dates:
        change = price * random.uniform(-0.02, 0.02)
        close = price + change
        open_p = close * random.uniform(0.99, 1.01)
        high = max(open_p, close) * random.uniform(1.0, 1.01)
        low = min(open_p, close) * random.uniform(0.99, 1.0)

        data.append({
            "time": date.strftime("%Y-%m-%d"),
            "open": round(open_p, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": int(random.uniform(1000, 100000))
        })
        price = close

    return data

@router.get("/symbols/search")
async def search_symbols(q: str = ""):
    """
    Mock symbol autocomplete.
    """
    universe = ["NIFTY", "BANKNIFTY", "RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK", "SBIN", "TATAMOTORS", "ITC"]
    q = q.upper()
    results = [s for s in universe if q in s]
    return results

@router.get("/spread/historical")
async def get_spread_historical(symbol1: str, symbol2: str, ratio: float = 1.0):
    """
    Returns spread history (Close1 - Ratio * Close2).
    """
    # Mock data directly for spread
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')

    spread_val = 0.0
    data = []

    for date in dates:
        change = random.uniform(-5, 5)
        spread_val += change
        # Mean reverting tendency
        spread_val -= spread_val * 0.05

        data.append({
            "time": date.strftime("%Y-%m-%d"),
            "value": round(spread_val, 2)
        })

    return data
