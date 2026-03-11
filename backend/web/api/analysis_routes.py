from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
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

class PrepareRequest(BaseModel):
    target_date: str
    end_date: Optional[str] = None

@router.post("/api/morning-report/prepare")
async def trigger_prepare_data(request: PrepareRequest):
    """Triggers the Celery task strictly to compute and save the DailyDerivativesAnalysis data."""
    from backend.ingest.tasks import prepare_morning_data_task
    task = prepare_morning_data_task.delay(request.target_date, request.end_date)
    return {"task_id": task.id, "status": "processing"}

class GenerateRequest(BaseModel):
    target_date: str
    author: str = "System"

@router.post("/api/morning-report/generate")
async def trigger_generate_report(request: GenerateRequest):
    """Triggers the Celery task to generate the PDF morning report using pre-calculated data."""
    from backend.ingest.tasks import generate_morning_report_task
    task = generate_morning_report_task.delay(request.target_date, request.author)
    return {"task_id": task.id, "status": "processing"}

@router.get("/api/morning-report/download/{target_date}")
async def download_report(target_date: str):
    """Serves the generated PDF report."""
    import os
    from fastapi.responses import FileResponse

    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../reports'))
    pdf_filename = f"Morning_Report_{target_date}.pdf"
    pdf_filepath = os.path.join(reports_dir, pdf_filename)

    if not os.path.exists(pdf_filepath):
        raise HTTPException(status_code=404, detail="Report not found. Generate it first.")

    return FileResponse(
        path=pdf_filepath,
        filename=pdf_filename,
        media_type='application/pdf'
    )

@router.get("/api/morning-report/list")
async def list_reports():
    """Lists all previously generated PDF reports."""
    import os
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../reports'))
    if not os.path.exists(reports_dir):
        return {"reports": []}

    reports = []
    for f in os.listdir(reports_dir):
        if f.endswith('.pdf') and f.startswith('Morning_Report_'):
            date_str = f.replace('Morning_Report_', '').replace('.pdf', '')
            reports.append({
                "filename": f,
                "date": date_str,
                "url": f"/api/morning-report/download/{date_str}"
            })

    # Sort newest first
    reports.sort(key=lambda x: x["date"], reverse=True)
    return {"reports": reports}

@router.get("/api/morning-report/status/{task_id}")
async def check_task_status(task_id: str):
    from backend.celery_worker import app as celery_app
    from celery.result import AsyncResult
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == 'PENDING':
        return {"state": task_result.state, "status": "Pending"}
    elif task_result.state == 'SUCCESS':
        return {"state": task_result.state, "result": task_result.result}
    elif task_result.state == 'FAILURE':
        return {"state": task_result.state, "error": str(task_result.info)}
    else:
        return {"state": task_result.state, "status": task_result.info}

@router.get("/api/morning-report/data/{target_date}")
async def get_report_data(target_date: str, db: Session = Depends(get_db)):
    from backend.ingest.nse_models import DailyDerivativesAnalysis
    from fastapi.concurrency import run_in_threadpool

    def fetch_data():
        return db.query(DailyDerivativesAnalysis).filter(
            DailyDerivativesAnalysis.trade_date == target_date
        ).order_by(DailyDerivativesAnalysis.atm_iv_near.desc().nulls_last()).all()

    records = await run_in_threadpool(fetch_data)

    if not records:
        return []

    result = []
    for r in records:
        d = dict(r.__dict__)
        d.pop('_sa_instance_state', None)
        result.append(d)

    return result

@router.get("/api/morning-report/timeseries")
async def get_report_timeseries(symbol: str, limit: int = 300, db: Session = Depends(get_db)):
    from backend.ingest.nse_models import DailyDerivativesAnalysis
    from fastapi.concurrency import run_in_threadpool

    def fetch_ts():
        return db.query(DailyDerivativesAnalysis).filter(
            DailyDerivativesAnalysis.symbol == symbol.upper()
        ).order_by(DailyDerivativesAnalysis.trade_date.desc()).limit(limit).all()

    records = await run_in_threadpool(fetch_ts)

    if not records:
        return []

    result = []
    for r in records:
        d = dict(r.__dict__)
        d.pop('_sa_instance_state', None)
        d['trade_date'] = str(d['trade_date'])
        result.append(d)

    return result

@router.get("/api/market-activity/dynamic-chart/{symbol}")
async def get_dynamic_chart_data(symbol: str, db: Session = Depends(get_db)):
    """
    Fetches 500 days of dynamic chart data for the UI Multi-Axis Tech Chart (Tile 3/4).
    Returns Candlesticks (OHLC), Volume, ATR (14d), Donchian Channel (20d), and Near Month Future OI.
    """
    from sqlalchemy import text
    import pandas as pd
    import numpy as np

    symbol = symbol.upper()

    # 1. Fetch 500 days of Cash Market Data (OHLC, Volume)
    cash_query = text("""
        SELECT trade_date, open_price, high_price, low_price, close_price, total_traded_qty as volume
        FROM bhavcopy_eq
        WHERE symbol = :sym AND series = 'EQ'
        ORDER BY trade_date ASC
        LIMIT 500
    """)
    cash_results = db.execute(cash_query, {"sym": symbol}).fetchall()

    if not cash_results:
        # Fallback to near futures for indices or stocks without EQ data
        fo_query = text("""
            SELECT * FROM (
                SELECT DISTINCT ON (trade_date) trade_date, open_price, high_price, low_price, close_price, total_trading_vol as volume
                FROM bhavcopy_fo
                WHERE ticker_symb = :sym AND instrument_type IN ('FUTIDX', 'FUTSTK')
                ORDER BY trade_date ASC, expiry_date ASC
            ) AS distinct_dates
            ORDER BY trade_date ASC
            LIMIT 500
        """)
        cash_results = db.execute(fo_query, {"sym": symbol}).fetchall()

    if not cash_results:
        raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

    df = pd.DataFrame(cash_results, columns=['trade_date', 'open', 'high', 'low', 'close', 'volume'])
    df['trade_date'] = pd.to_datetime(df['trade_date'])

    # Handle duplicate dates in fallback data by taking the first (nearest expiry)
    df = df.sort_values(['trade_date']).groupby('trade_date').first().reset_index()
    df.set_index('trade_date', inplace=True)

    # 2. Calculate ATR (14-day Wilder's)
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['atr_14'] = df['tr'].ewm(alpha=1/14, adjust=False).mean()
    # Convert ATR to % of price
    df['atr_14_pct'] = np.where(df['close'] > 0, (df['atr_14'] / df['close']) * 100, 0)

    # 3. Calculate Donchian Channels (20-day) & MA20
    df['donchian_upper'] = df['high'].rolling(window=20).max()
    df['donchian_lower'] = df['low'].rolling(window=20).min()
    df['ma20'] = df['close'].rolling(window=20).mean()

    # 4. Fetch 500 days of Total Futures OI
    oi_query = text("""
        SELECT trade_date, SUM(open_interest) as total_oi
        FROM bhavcopy_fo
        WHERE ticker_symb = :sym AND instrument_type IN ('FUTIDX', 'FUTSTK')
        GROUP BY trade_date
        ORDER BY trade_date ASC
        LIMIT 500
    """)
    oi_results = db.execute(oi_query, {"sym": symbol}).fetchall()
    df_oi = pd.DataFrame(oi_results, columns=['trade_date', 'total_oi'])
    if not df_oi.empty:
        df_oi['trade_date'] = pd.to_datetime(df_oi['trade_date'])
        df_oi.set_index('trade_date', inplace=True)
        # Merge into main DF
        df = df.join(df_oi, how='left')
    else:
        df['total_oi'] = 0

    # Fill NaNs for JSON serialization
    df.fillna(0, inplace=True)

    # Prepare response arrays
    dates = df.index.strftime('%Y-%m-%d').tolist()
    # ECharts candlestick expects [open, close, lowest, highest]
    ohlc = df[['open', 'close', 'low', 'high']].values.tolist()

    return {
        "dates": dates,
        "ohlc": ohlc,
        "volume": df['volume'].tolist(),
        "ma20": df['ma20'].tolist(),
        "donchian_upper": df['donchian_upper'].tolist(),
        "donchian_lower": df['donchian_lower'].tolist(),
        "atr": df['atr_14_pct'].tolist(),
        "oi": df['total_oi'].tolist()
    }

@router.get("/api/market-activity/participant-oi")
async def get_participant_oi(db: Session = Depends(get_db)):
    from backend.ingest.nse_models import FAOParticipantOI

    # Get the last 252 trading days
    dates = db.query(FAOParticipantOI.trade_date).distinct().order_by(FAOParticipantOI.trade_date.desc()).limit(252).all()
    dates = [d[0] for d in dates]
    dates.sort() # chronological

    if not dates:
         return {"dates": [], "fii_net_long": [], "pro_net_long": [], "client_net_long": []}

    records = db.query(FAOParticipantOI).filter(FAOParticipantOI.trade_date.in_(dates)).all()

    import pandas as pd
    df = pd.DataFrame([{
        'date': r.trade_date,
        'client_type': r.client_type,
        'fut_idx_long': r.future_index_long,
        'fut_idx_short': r.future_index_short
    } for r in records])

    if df.empty:
         return {"dates": [], "fii_net_long": [], "pro_net_long": [], "client_net_long": []}

    df['net_long'] = df['fut_idx_long'] - df['fut_idx_short']

    pivot = df.pivot_table(index='date', columns='client_type', values='net_long', aggfunc='sum').fillna(0)
    pivot = pivot.reindex(pd.to_datetime(dates)).fillna(0)

    return {
        "dates": [d.strftime('%Y-%m-%d') for d in pivot.index],
        "fii_net_long": pivot.get('FII', pd.Series(0, index=pivot.index)).tolist(),
        "pro_net_long": pivot.get('PRO', pd.Series(0, index=pivot.index)).tolist(),
        "client_net_long": pivot.get('Client', pd.Series(0, index=pivot.index)).tolist()
    }

@router.get("/api/market-activity/cash-flow")
async def get_cash_market_flow(db: Session = Depends(get_db)):
    """
    Returns real FII/DII Cash Market Flow from the database over the last 252 days.
    """
    from backend.ingest.nse_models import FIIDIICash

    dates_query = db.query(FIIDIICash.trade_date).distinct().order_by(FIIDIICash.trade_date.desc()).limit(252).all()
    dates = [d[0] for d in dates_query]
    dates.sort()

    if not dates:
         return {"dates": [], "fii_net": [], "dii_net": []}

    records = db.query(FIIDIICash).filter(FIIDIICash.trade_date.in_(dates)).all()

    import pandas as pd
    df = pd.DataFrame([{
        'date': r.trade_date,
        'category': r.category,
        'net_value': r.net_value
    } for r in records])

    if df.empty:
         return {"dates": [], "fii_net": [], "dii_net": []}

    pivot = df.pivot_table(index='date', columns='category', values='net_value', aggfunc='sum').fillna(0)
    pivot = pivot.reindex(pd.to_datetime(dates)).fillna(0)

    return {
        "dates": [d.strftime('%Y-%m-%d') for d in pivot.index],
        "fii_net": pivot.get('FII', pd.Series(0, index=pivot.index)).tolist(),
        "dii_net": pivot.get('DII', pd.Series(0, index=pivot.index)).tolist()
    }
