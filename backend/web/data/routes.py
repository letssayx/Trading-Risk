from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy

router = APIRouter()

# Mock Data Generation (Fallback)
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

def fetch_historical_data(symbol: str, days: int, db: Session):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    rows = db.query(Bhavcopy).filter(
        Bhavcopy.symbol == symbol,
        Bhavcopy.trade_date >= start_date
    ).order_by(Bhavcopy.trade_date.asc()).all()

    if rows:
        data = []
        for r in rows:
            data.append({
                "time": r.trade_date.strftime("%Y-%m-%d"),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.total_traded_qty
            })
        return data
    return None

@router.get("/api/historical/{symbol}")
async def get_historical_data(symbol: str, days: int = 365, db: Session = Depends(get_db)):
    data = fetch_historical_data(symbol, days, db)
    if data:
        return data
    # Fallback to mock if no data
    return generate_ohlc(symbol, days)

@router.get("/api/spread/historical")
async def get_spread_historical(symbol1: str, symbol2: str, ratio: float = 1.0, days: int = 365):
    # Note: Implementing full DB spread logic is complex due to date alignment.
    # For now, sticking to mock for spread unless we want to fetch both and align.
    # Let's keep mock for speed as per user request scope, but noted for future.

    data1 = generate_ohlc(symbol1, days)
    data2 = generate_ohlc(symbol2, days)

    spread_data = []
    min_len = min(len(data1), len(data2))

    for i in range(min_len):
        d1 = data1[i]
        d2 = data2[i]
        val = d1["close"] - (ratio * d2["close"])
        spread_data.append({
            "time": d1["time"],
            "value": round(val, 2)
        })

    return spread_data

@router.get("/api/symbols/search")
async def search_symbols(q: str, db: Session = Depends(get_db)):
    if not q:
        return []

    # Search in DB
    results = db.query(Bhavcopy.symbol).filter(
        Bhavcopy.symbol.ilike(f"{q}%")
    ).distinct().limit(10).all()

    symbols = [r[0] for r in results]

    # Fallback/Add standard indices if missing/empty DB
    defaults = ["NIFTY", "BANKNIFTY", "RELIANCE"]
    for d in defaults:
        if q.upper() in d and d not in symbols:
            symbols.append(d)

    return symbols[:10]

@router.get("/api/edge")
async def get_trading_edge(db: Session = Depends(get_db)):
    # Try to get latest date stats from DB
    latest_date_row = db.query(Bhavcopy.trade_date).order_by(Bhavcopy.trade_date.desc()).first()

    if latest_date_row:
        date = latest_date_row[0]

        # Calculate Advance/Decline
        total = db.query(Bhavcopy).filter(Bhavcopy.trade_date == date).count()
        advances = db.query(Bhavcopy).filter(
            Bhavcopy.trade_date == date,
            Bhavcopy.close > Bhavcopy.open
        ).count()

        sentiment = "Bullish" if advances > (total/2) else "Bearish"

        # Calculate Turnover (Mock FII Flow proxy)
        turnover = db.query(func.sum(Bhavcopy.total_traded_val)).filter(Bhavcopy.trade_date == date).scalar() or 0
        turnover_cr = round(turnover / 10000000, 2) # Convert to Crores

        return {
            "sentiment": sentiment,
            "regime": "Trending" if abs(advances - (total/2)) > (total * 0.1) else "Sideways",
            "pe_ratio": 24.5, # Placeholder
            "iv_percentile": 45, # Placeholder
            "fii_flow": f"{turnover_cr} Cr (Turnover)" # Proxy
        }

    # Mock Fallback
    return {
        "sentiment": "Neutral",
        "regime": "No Data",
        "pe_ratio": 0,
        "iv_percentile": 0,
        "fii_flow": "0 Cr"
    }
