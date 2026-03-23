from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from datetime import datetime
import pandas as pd
import json

from backend.infrastructure.db import get_db
from backend.ingest.nse_models import DailyDerivativesAnalysis, BhavcopyFO

router = APIRouter()

@router.get("/api/data/derivatives/mwpl_historical")
async def get_mwpl_historical(db: Session = Depends(get_db)):
    """
    Fetches the last 14 trading days of mwpl_array data from daily_derivatives_analysis.
    Also retrieves the EQ close and calculate the Fut1 close.
    """
    from backend.ingest.nse_models import BhavcopyEQ
    # Find the last 14 unique trading dates in daily_derivatives_analysis
    dates_query = db.query(DailyDerivativesAnalysis.trade_date).distinct().order_by(DailyDerivativesAnalysis.trade_date.desc()).limit(14).all()
    if not dates_query:
        return {"data": {}}

    dates = [d[0] for d in dates_query]

    # Query data for these dates where mwpl_array is not null and not empty
    records = db.query(
        DailyDerivativesAnalysis.trade_date,
        DailyDerivativesAnalysis.symbol,
        DailyDerivativesAnalysis.mwpl_array,
        DailyDerivativesAnalysis.close_price,
        BhavcopyEQ.close_price.label('eq_close_price')
    ).outerjoin(
        BhavcopyEQ,
        (DailyDerivativesAnalysis.symbol == BhavcopyEQ.symbol) &
        (DailyDerivativesAnalysis.trade_date == BhavcopyEQ.trade_date) &
        (BhavcopyEQ.series == 'EQ')
    ).filter(
        DailyDerivativesAnalysis.trade_date.in_(dates),
        DailyDerivativesAnalysis.mwpl_array != None
    ).all()

    result = {}
    for r in records:
        sym = r.symbol
        if sym not in result:
            result[sym] = []

        # Parse mwpl_array properly
        parsed_arr = []
        try:
            arr = r.mwpl_array
            if isinstance(arr, str):
                arr = json.loads(arr)
            if isinstance(arr, list):
                for item in arr:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            parsed_arr.append({k: float(v)})
                    elif isinstance(item, (int, float)):
                        parsed_arr.append({"Client": float(item)})
        except Exception:
            pass

        if parsed_arr:
            result[sym].append({
                "date": str(r.trade_date),
                "eq_close": float(r.eq_close_price) if r.eq_close_price else 0.0,
                "fut1_close": float(r.close_price) if r.close_price else 0.0,
                "mwpl_array": parsed_arr
            })

    # Sort dates descending for each symbol
    for sym in result:
        result[sym].sort(key=lambda x: x["date"], reverse=True)

    return {"data": result}

@router.get("/api/data/derivatives/marketwatch")
async def get_marketwatch(db: Session = Depends(get_db)):
    """
    Fetches Market Watch data for all F&O symbols.
    Returns current EQ price, Corporate Action (Ex-date), and the next 3 unexpired future contracts
    (Fut1, Fut2, Fut3) with their Price, Volume, OI, ATP, DTE, etc.
    """
    from backend.ingest.nse_models import BhavcopyEQ
    from backend.domain.market.models import Bhavcopy
    import datetime

    # Get latest F&O trading date
    latest_fo_date = db.query(BhavcopyFO.trade_date).order_by(desc(BhavcopyFO.trade_date)).first()
    if not latest_fo_date:
        return {"data": {}}
    latest_fo_date = latest_fo_date[0]

    # 1. Fetch all EQ data for the latest date
    eq_records = db.query(
        BhavcopyEQ.symbol,
        BhavcopyEQ.close_price,
        BhavcopyEQ.total_traded_qty,
        BhavcopyEQ.avg_price
    ).filter(
        BhavcopyEQ.trade_date == latest_fo_date,
        BhavcopyEQ.series == 'EQ'
    ).all()

    eq_map = {r.symbol: {"price": float(r.close_price) if r.close_price else 0.0,
                         "vol": int(r.total_traded_qty) if r.total_traded_qty else 0,
                         "atp": float(r.avg_price) if r.avg_price else 0.0} for r in eq_records}

    # Also add indices from HistoricalIndexData
    from backend.ingest.nse_models import HistoricalIndexData
    idx_records = db.query(
        HistoricalIndexData.index_name,
        HistoricalIndexData.close_price,
        HistoricalIndexData.total_traded_qty
    ).filter(
        HistoricalIndexData.trade_date == latest_fo_date
    ).all()

    for r in idx_records:
        sym = r.index_name.replace('NIFTY 50', 'NIFTY').replace('NIFTY BANK', 'BANKNIFTY').replace('NIFTY FIN SERVICE', 'FINNIFTY').replace('NIFTY MID SELECT', 'MIDCPNIFTY')
        eq_map[sym] = {
            "price": float(r.close_price) if r.close_price else 0.0,
            "vol": int(r.total_traded_qty) if r.total_traded_qty else 0,
            "atp": 0.0
        }

    # 2. Fetch active Futures data
    fut_records = db.query(
        BhavcopyFO.ticker_symb,
        BhavcopyFO.expiry_date,
        BhavcopyFO.close_price,
        BhavcopyFO.total_trading_vol,
        BhavcopyFO.open_interest,
        BhavcopyFO.change_in_oi
    ).filter(
        BhavcopyFO.trade_date == latest_fo_date,
        BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX'])
    ).all()

    # Organize futures by symbol and sort by expiry
    fut_map = {}
    for r in fut_records:
        sym = r.ticker_symb
        if sym not in fut_map:
            fut_map[sym] = []

        dte = (r.expiry_date - latest_fo_date).days if r.expiry_date else 0
        fut_map[sym].append({
            "expiry": str(r.expiry_date),
            "price": float(r.close_price) if r.close_price else 0.0,
            "vol": int(r.total_trading_vol) if r.total_trading_vol else 0,
            "oi": int(r.open_interest) if r.open_interest else 0,
            "chg_oi": int(r.change_in_oi) if r.change_in_oi else 0,
            "dte": dte
        })

    for sym in fut_map:
        fut_map[sym].sort(key=lambda x: x["expiry"])

    # 3. Fetch Corporate Actions (Dividends with upcoming ex-dates)
    # Just look for active dividends within next month
    ca_map = {}
    try:
        from backend.ingest.nse_models import CorporateAction
        import datetime
        next_month = latest_fo_date + datetime.timedelta(days=30)
        ca_records = db.query(
            CorporateAction.symbol,
            CorporateAction.ex_date,
            CorporateAction.purpose
        ).filter(
            CorporateAction.ex_date >= latest_fo_date,
            CorporateAction.ex_date <= next_month,
            CorporateAction.parsed_dividend_amount != None
        ).all()
        for r in ca_records:
            ca_map[r.symbol] = f"{r.ex_date.strftime('%d-%b')} Div"
    except Exception:
        pass

    result = {}
    # Only return symbols that exist in F&O (i.e. they have futures)
    for sym, futures in fut_map.items():
        if len(futures) == 0:
            continue

        eq_data = eq_map.get(sym, {"price": 0.0, "vol": 0, "atp": 0.0})

        # Prepare F1, F2, F3
        futs = futures[:3]

        # Calculate BPS and Yield
        for i in range(len(futs)):
            futs[i]["bps"] = 0.0
            futs[i]["yield"] = 0.0

            base_price = eq_data["price"] if i == 0 else futs[i-1]["price"]
            days = futs[i]["dte"] if i == 0 else (futs[i]["dte"] - futs[i-1]["dte"])

            if base_price > 0:
                futs[i]["bps"] = ((futs[i]["price"] - base_price) / base_price) * 10000

            if days > 0:
                futs[i]["yield"] = (futs[i]["bps"] / 10000) * (365 / days) * 100

        result[sym] = {
            "eq": {
                "price": eq_data["price"],
                "vol": eq_data["vol"],
                "atp": eq_data["atp"],
                "ca": ca_map.get(sym, "")
            },
            "futures": futs
        }

    return {"data": result}
