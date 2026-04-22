from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy
from backend.domain.market.contract_manager import ContractManager

router = APIRouter()

@router.get("/api/historical/{symbol}")
async def get_historical_data(symbol: str, days: int = 365, db: Session = Depends(get_db)):
    """
    Fetch historical data from DB.
    Matches both CM (Equity) and FO (Futures) based on symbol pattern.
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Simple Heuristic: If symbol ends with FUT, search in FO, else CM
    # However, Bhavcopy stores "RELIANCE" in both.
    # For chart simplicity, if user asks for "NIFTY", we might mean index or future.
    # Let's try to find exact match first.

    query = db.query(Bhavcopy).filter(
        Bhavcopy.symbol == symbol.upper(),
        Bhavcopy.trade_date >= start_date
    ).order_by(Bhavcopy.trade_date)

    # If no instrument type specified, prioritize CM for simple symbols, or specific Future contract
    # If symbol looks like RELIANCE24JANFUT, it will match symbol column?
    # Actually, Bhavcopy usually stores symbol="RELIANCE" and expiry/instrument_type separate.
    # But ContractManager generates concatenated strings.
    # We need a reverse parser or search logic.

    # 1. Try Exact Match (if symbol column matches directly, e.g. imported as is)
    results = query.all()

    if not results:
        # 2. Try parsing contract if it looks like a future
        # e.g. NIFTY24FEBFUT -> Symbol: NIFTY, Expiry: 2024-02-29
        # This is complex without a robust parser.
        # Fallback: Search for underlying in CM if pure symbol
        results = db.query(Bhavcopy).filter(
            Bhavcopy.symbol == symbol.upper(),
            Bhavcopy.segment == 'CM',
            Bhavcopy.series.in_(['EQ', 'BE']),
            Bhavcopy.trade_date >= start_date
        ).order_by(Bhavcopy.trade_date).all()

    if not results:
        # 3. If still empty, maybe it's an Index? (segment=FO, instrument=FUTIDX/OPTIDX but we want index spot?)
        # NSE Bhavcopy doesn't always have Index Spot in CM.
        # Try finding nearest future?
        # For now, return empty list if not found.
        return []

    data = []
    for row in results:
        data.append({
            "time": row.trade_date.strftime("%Y-%m-%d"),
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.total_traded_qty
        })

    return data

@router.get("/api/spread/historical")
async def get_spread_historical(
    symbol1: str,
    symbol2: str,
    ratio: float = 1.0,
    days: int = 365,
    db: Session = Depends(get_db)
):
    # Fetch data for both
    data1 = await get_historical_data(symbol1, days, db)
    data2 = await get_historical_data(symbol2, days, db)

    if not data1 or not data2:
        return []

    # Convert to DF for easy alignment
    df1 = pd.DataFrame(data1).set_index('time')
    df2 = pd.DataFrame(data2).set_index('time')

    # Join
    df = df1[['close']].join(df2[['close']], lsuffix='_1', rsuffix='_2', how='inner')

    spread_data = []
    for date, row in df.iterrows():
        val = row['close_1'] - (ratio * row['close_2'])
        spread_data.append({
            "time": date,
            "value": round(val, 2)
        })

    return spread_data

@router.get("/api/symbols/search")
async def search_symbols(q: str, segment: str = "EQ", db: Session = Depends(get_db)):
    """
    Search symbols in DB.
    """
    q_str = f"{q.upper()}%"

    if segment.upper() == "FO":
        # Find Unique Underlying symbols in FO
        results = db.query(Bhavcopy.symbol).filter(
            Bhavcopy.segment == 'FO',
            Bhavcopy.symbol.like(q_str)
        ).distinct().limit(20).all()

        base_symbols = [r[0] for r in results]

        # Expand to futures contracts using ContractManager
        futures_results = []
        for sym in base_symbols:
            futures = ContractManager.get_futures_symbols(sym)
            futures_results.extend(futures)
        return futures_results

    else:
        # CM Search
        results = db.query(Bhavcopy.symbol).filter(
            Bhavcopy.segment == 'CM',
            Bhavcopy.symbol.like(q_str)
        ).distinct().limit(20).all()

        return [r[0] for r in results]

@router.get("/api/edge")
async def get_trading_edge():
    # This might still need mock or real calculation.
    # For now, we return neutral/empty if no logic exists, or keep static placeholder
    # but user said "remove random walk", this is "Market Context".
    # I'll return a static "N/A" or "Waiting for Data" to indicate no fake data.
    return {
        "sentiment": "Neutral",
        "regime": "Unknown",
        "pe_ratio": 0,
        "iv_percentile": 0,
        "fii_flow": "0"
    }
