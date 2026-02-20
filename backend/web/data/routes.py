from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from backend.infrastructure.db import get_db
from backend.domain.market.service import MarketDataService

router = APIRouter()

@router.get("/api/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    days: int = 365,
    db: Session = Depends(get_db)
):
    """
    Get historical OHLC data from real Bhavcopy records.
    Supports both Underlying (e.g. RELIANCE) and Contracts (e.g. RELIANCE24FEBFUT).
    """
    data = MarketDataService.get_daily_ohlc(db, symbol, days=days)
    if not data:
        # If no data found, return empty list rather than 404 to avoid breaking charts
        return []
    return data

@router.get("/api/spread/historical")
async def get_spread_historical(
    symbol1: str,
    symbol2: str,
    ratio: float = 1.0,
    days: int = 365,
    db: Session = Depends(get_db)
):
    """
    Calculate spread history (Price1 - Ratio * Price2) from real data.
    """
    data1 = MarketDataService.get_daily_ohlc(db, symbol1, days=days)
    data2 = MarketDataService.get_daily_ohlc(db, symbol2, days=days)

    if not data1 or not data2:
        return []

    # Align dates
    df1 = pd.DataFrame(data1).set_index('time')
    df2 = pd.DataFrame(data2).set_index('time')

    # Inner join on dates
    aligned = df1.join(df2, lsuffix='_1', rsuffix='_2', how='inner')

    spread_data = []
    for date_str, row in aligned.iterrows():
        # Calculate spread: P1 - Ratio * P2
        # Use close price
        val = row['close_1'] - (ratio * row['close_2'])

        spread_data.append({
            "time": date_str,
            "value": round(val, 2)
        })

    return spread_data

@router.get("/api/symbols/search")
async def search_symbols(
    q: str,
    segment: str = "EQ",
    db: Session = Depends(get_db)
):
    """
    Search for symbols or contracts in the database.
    segment: 'EQ' (Equity/CM) or 'FO' (Futures/Derivatives)
    """
    return MarketDataService.search_symbols(db, q, segment)

@router.get("/api/edge")
async def get_trading_edge(db: Session = Depends(get_db)):
    """
    Get Market Context.
    Currently returns basic availability info or 'N/A' as we don't have
    calculated Greeks/Sentiment engines connected to real data yet.
    """
    latest_date = MarketDataService.get_latest_date(db)

    return {
        "sentiment": "Neutral", # Placeholder until calculated
        "regime": "N/A",
        "pe_ratio": 0.0,
        "iv_percentile": 0,
        "fii_flow": "N/A",
        "latest_data_date": latest_date.strftime("%Y-%m-%d") if latest_date else "None"
    }
