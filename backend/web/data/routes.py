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
from backend.domain.market.contract_manager import ContractManager
from backend.infrastructure.upstox_client import upstox_client

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

def fetch_historical_data(symbol: str, segment: str, days: int, db: Session, expiry_pos: int = 1):
    """
    Fetches historical data.
    If segment is FO, constructs a rolling futures series based on `expiry_pos` (1=Near, 2=Next, 3=Far).
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    if segment == 'FO':
        # Use ContractManager to stitch rolling futures
        # expiry_pos defaults to 1 (Near Month)
        continuous_data = ContractManager.get_continuous_future(db, symbol, expiry_pos, start_date, end_date)
        if continuous_data:
            data = []
            for item in continuous_data:
                data.append({
                    "time": item["date"].strftime("%Y-%m-%d"),
                    "symbol": item.get("contract_symbol"), # Forward mapped symbol
                    "open": item["open"],
                    "high": item["high"],
                    "low": item["low"],
                    "close": item["close"],
                    "volume": item["volume"],
                    "oi": item.get("oi", 0),
                    "expiry": item["expiry"].strftime("%Y-%m-%d") if item.get("expiry") else None
                })
            return data
        return None

    # Standard CM Logic
    query = db.query(Bhavcopy).filter(
        Bhavcopy.symbol == symbol,
        Bhavcopy.trade_date >= start_date,
        Bhavcopy.segment == segment
    )

    if segment == 'CM':
        query = query.filter(Bhavcopy.series == 'EQ')

    query = query.order_by(Bhavcopy.trade_date.asc())
    rows = query.all()

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
async def get_historical_data(symbol: str, segment: str = "CM", expiry: int = 1, days: int = 365, db: Session = Depends(get_db)):
    data = fetch_historical_data(symbol, segment, days, db, expiry_pos=expiry)
    if data:
        return data
    # Fallback to Upstox
    if upstox_client.is_configured():
        # Map symbol to instrument key?
        # Assuming user enters instrument key or standard symbol
        # Upstox needs format like 'NSE_EQ|INE002A01018' or similar.
        # For simple demo, try 'NSE_EQ|{symbol}'
        key = upstox_client.get_instrument_key(symbol)
        interval = 'day'
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        upstox_data = upstox_client.get_historical_candles(key, interval, to_date, from_date)
        if upstox_data:
            return upstox_data

    # Fallback to mock if no data
    # Ideally should return empty if "no fake data" requested, but let's keep mock as last resort
    # to prevent broken UI if no DB and no Upstox.
    # The user said "if data not available then dont show".
    # So if upstox fails and DB empty, return []?
    # Or mock only if absolutely necessary?
    # Let's return [] to respect "donot use false prices".
    return []

@router.get("/api/spread/historical")
async def get_spread_historical(symbol1: str, symbol2: str, ratio: float = 1.0, days: int = 365, db: Session = Depends(get_db)):
    # Try fetching real data for both legs
    # Defaulting to CM segment for spread tools usually
    data1 = fetch_historical_data(symbol1, "CM", days, db)
    data2 = fetch_historical_data(symbol2, "CM", days, db)

    if not data1 or not data2:
        return []

    # Convert to dict for alignment
    d1_map = {d["time"]: d["close"] for d in data1}
    d2_map = {d["time"]: d["close"] for d in data2}

    common_dates = sorted(list(set(d1_map.keys()) & set(d2_map.keys())))

    spread_data = []
    for date in common_dates:
        val = d1_map[date] - (ratio * d2_map[date])
        spread_data.append({
            "time": date,
            "value": round(val, 2)
        })

    return spread_data

@router.get("/api/symbols/search")
async def search_symbols(q: str, segment: str = "CM", db: Session = Depends(get_db)):
    if not q:
        return []

    # Search in DB with Segment priority
    # If FO, we prioritize fetching the base symbol, but we could also return full contracts if q matches?
    # User requirement: "Bhavcopy is showing BDL26FEBFUT".
    # If user types "BDL" in FO mode, we should suggest "BDL".
    # If they type "BDL26", we should suggest "BDL26FEBFUT".

    query = db.query(Bhavcopy.symbol).filter(
        Bhavcopy.symbol.ilike(f"{q}%"),
        Bhavcopy.segment == segment
    )

    # For CM, just distinct symbols
    if segment == "CM":
        results = query.distinct().limit(10).all()
        symbols = [r[0] for r in results]
    else:
        # For FO, we might have many contracts per base symbol.
        # Ideally we return distinct base symbols if q is short, or specific contracts if q is long.
        # But 'symbol' column in Bhavcopy for FO is typically the base symbol (e.g. 'RELIANCE') in UDIFF?
        # WAIT. In UDIFF, 'TckrSymb' (symbol) is 'RELIANCE'. The contract descriptor is built from expiry.
        # UNLESS the user data has 'RELIANCE26FEBFUT' in the symbol column?
        # The user said: "Bhavcopy is showing BDL26FEBFUT". This implies for some data sources, symbol IS the contract.
        # Our loader maps 'TckrSymb' -> 'symbol'.
        # If the user's import has full names, then distinct search works.
        # If it has base names, then we just return base names.
        # We will return whatever is in the 'symbol' column.
        results = query.distinct().limit(10).all()
        symbols = [r[0] for r in results]

    # Fallback/Add standard indices
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
            "pe_ratio": "--",
            "iv_percentile": "--",
            "fii_flow": f"{turnover_cr} Cr (Turnover)"
        }

    # Upstox Fallback?
    # Edge needs market breadth which is hard from single quotes.
    # But if Upstox connected, we could return "Realtime" status?

    if upstox_client.is_configured():
        return {
            "sentiment": "Unknown (Live)",
            "regime": "Live Feed Active",
            "pe_ratio": "--",
            "iv_percentile": "--",
            "fii_flow": "Realtime"
        }

    # No Data
    return {
        "sentiment": "No Data",
        "regime": "Disconnected",
        "pe_ratio": 0,
        "iv_percentile": 0,
        "fii_flow": "0 Cr"
    }
