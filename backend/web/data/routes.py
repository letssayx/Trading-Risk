from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np

router = APIRouter()

# Mock Data Generation
def generate_ohlc(symbol: str, days: int = 365):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D') # Daily for now

    base_price = 1000.0 + random.random() * 1000
    data = []

    current_price = base_price
    for date in dates:
        if date.weekday() >= 5: continue # Skip weekends

        open_p = current_price
        high_p = open_p * (1 + random.random() * 0.02)
        low_p = open_p * (1 - random.random() * 0.02)
        close_p = low_p + (high_p - low_p) * random.random()
        volume = int(random.random() * 1000000)

        data.append({
            "time": date.strftime("%Y-%m-%d"),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": volume
        })
        current_price = close_p

    return data

@router.get("/api/historical/{symbol}")
async def get_historical_data(symbol: str, days: int = 365):
    return generate_ohlc(symbol, days)

@router.get("/api/spread/historical")
async def get_spread_historical(symbol1: str, symbol2: str, ratio: float = 1.0, days: int = 365):
    data1 = generate_ohlc(symbol1, days)
    data2 = generate_ohlc(symbol2, days)

    # Align dates (simple assume same length for mock)
    spread_data = []
    min_len = min(len(data1), len(data2))

    for i in range(min_len):
        d1 = data1[i]
        d2 = data2[i]

        # Calculate spread: P1 - Ratio * P2
        val = d1["close"] - (ratio * d2["close"])

        spread_data.append({
            "time": d1["time"],
            "value": round(val, 2)
        })

    return spread_data

@router.get("/api/symbols/search")
async def search_symbols(q: str):
    # Mock search
    all_symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFC", "SBIN", "TATAMOTORS", "WIPRO", "ADANIENT"]
    results = [s for s in all_symbols if q.upper() in s]
    return results

@router.get("/api/edge")
async def get_trading_edge():
    # Mock Market Context
    return {
        "sentiment": "Bullish",
        "regime": "Trending",
        "pe_ratio": 24.5,
        "iv_percentile": 45,
        "fii_flow": "+1200 Cr"
    }
