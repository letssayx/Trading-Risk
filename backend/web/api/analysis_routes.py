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
        from sqlalchemy import case
        return db.query(DailyDerivativesAnalysis).filter(
            DailyDerivativesAnalysis.trade_date == target_date
        ).order_by(
            case(
                (DailyDerivativesAnalysis.symbol == 'NIFTY', 0),
                (DailyDerivativesAnalysis.symbol == 'BANKNIFTY', 1),
                else_=2
            ),
            DailyDerivativesAnalysis.atm_iv_near.desc().nulls_last()
        ).all()

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
        return {"dates": []}
    else:
        df = pd.DataFrame(cash_results, columns=['trade_date', 'open', 'high', 'low', 'close', 'volume'])
        df['trade_date'] = pd.to_datetime(df['trade_date'])

        # Handle duplicate dates in fallback data by taking the first (nearest expiry)
        df = df.sort_values(['trade_date']).groupby('trade_date').first().reset_index()
        df.set_index('trade_date', inplace=True)

    # 2. Technical Indicators
    # a. SMA 20 & Bollinger Bands (1, 2, 3 Sigma)
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['std20'] = df['close'].rolling(window=20).std()

    df['bb_upper_1'] = df['ma20'] + (df['std20'] * 1)
    df['bb_lower_1'] = df['ma20'] - (df['std20'] * 1)
    df['bb_upper_2'] = df['ma20'] + (df['std20'] * 2)
    df['bb_lower_2'] = df['ma20'] - (df['std20'] * 2)
    df['bb_upper_3'] = df['ma20'] + (df['std20'] * 3)
    df['bb_lower_3'] = df['ma20'] - (df['std20'] * 3)

    # b. RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))

    # c. MACD (12, 26, 9)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # 3. Fetch 500 days of Total Futures OI
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

    # 4. Retrieve Actual PCR & IV Data
    # Fetch historical PCR and IV strictly from the DB instead of simulating
    # If option data is not present, we default to 0 (no fallback simulation)
    opt_query = text("""
        SELECT
            trade_date,
            SUM(CASE WHEN option_type = 'CE' THEN open_interest ELSE 0 END) as ce_oi,
            SUM(CASE WHEN option_type = 'PE' THEN open_interest ELSE 0 END) as pe_oi
        FROM bhavcopy_fo
        WHERE ticker_symb = :sym AND instrument_type IN ('OPTIDX', 'OPTSTK')
        GROUP BY trade_date
    """)
    opt_results = db.execute(opt_query, {"sym": symbol}).fetchall()
    if opt_results:
        df_opt = pd.DataFrame(opt_results, columns=['trade_date', 'ce_oi', 'pe_oi'])
        df_opt['trade_date'] = pd.to_datetime(df_opt['trade_date'])
        df_opt.set_index('trade_date', inplace=True)
        df_opt['pcr'] = np.where(df_opt['ce_oi'] > 0, df_opt['pe_oi'] / df_opt['ce_oi'], 0)
        df = df.join(df_opt[['pcr']], how='left')
    else:
        df['pcr'] = 0

    # For true IV, we would fetch from FOVolatility. For now, strictly default to 0 if we don't fetch it,
    # instead of generating random numbers.
    vol_query = text("""
        SELECT trade_date, daily_volatility as iv
        FROM fo_volatility
        WHERE symbol = :sym
    """)
    try:
        vol_results = db.execute(vol_query, {"sym": symbol}).fetchall()
        if vol_results:
            df_vol = pd.DataFrame(vol_results, columns=['trade_date', 'iv'])
            df_vol['trade_date'] = pd.to_datetime(df_vol['trade_date'])
            df_vol.set_index('trade_date', inplace=True)
            df = df.join(df_vol[['iv']], how='left')
        else:
            df['iv'] = 0
    except Exception:
        df['iv'] = 0

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
        "bb_upper_1": df['bb_upper_1'].tolist(),
        "bb_lower_1": df['bb_lower_1'].tolist(),
        "bb_upper_2": df['bb_upper_2'].tolist(),
        "bb_lower_2": df['bb_lower_2'].tolist(),
        "bb_upper_3": df['bb_upper_3'].tolist(),
        "bb_lower_3": df['bb_lower_3'].tolist(),
        "rsi_14": df['rsi_14'].tolist(),
        "macd": df['macd'].tolist(),
        "macd_signal": df['macd_signal'].tolist(),
        "macd_hist": df['macd_hist'].tolist(),
        "total_oi": df['total_oi'].tolist(),
        "pcr": df['pcr'].tolist(),
        "iv": df['iv'].tolist()
    }

@router.get("/api/market-activity/participant-oi")
async def get_participant_oi(days: int = 30, db: Session = Depends(get_db)):
    from backend.ingest.nse_models import FAOParticipantOI

    try:
        # Get the last X trading days
        dates = db.query(FAOParticipantOI.trade_date).distinct().order_by(FAOParticipantOI.trade_date.desc()).limit(days).all()
        dates = [d[0] for d in dates]
        dates.sort() # chronological
    except Exception as e:
        dates = []

    import pandas as pd
    import numpy as np
    from datetime import date, timedelta

    if not dates:
         return {"dates": []}

    records = db.query(FAOParticipantOI).filter(FAOParticipantOI.trade_date.in_(dates)).all()

    df = pd.DataFrame([{
        'date': r.trade_date,
        'client_type': r.client_type,
        'fut_idx_net': r.future_index_long - r.future_index_short,
        'fut_stk_net': r.future_stock_long - r.future_stock_short,
        'opt_idx_ce_net': r.option_index_call_long - r.option_index_call_short,
        'opt_idx_pe_net': r.option_index_put_long - r.option_index_put_short,
        'opt_stk_ce_net': r.option_stock_call_long - r.option_stock_call_short,
        'opt_stk_pe_net': r.option_stock_put_long - r.option_stock_put_short
    } for r in records])

    if df.empty:
         return {"dates": []}


    # Normalize client types (e.g. Map 'Pro' -> 'PRO' if necessary to avoid missing data)
    df['client_type'] = df['client_type'].str.upper()
    df.loc[df['client_type'] == 'PRO', 'client_type'] = 'Pro'
    df.loc[df['client_type'] == 'CLIENT', 'client_type'] = 'Client'

    # Handle pandas duplicate index/axis reindex issues
    try:
        pivot_idx = df.pivot_table(index='date', columns='client_type', values='fut_idx_net', aggfunc='sum').fillna(0)
        pivot_stk = df.pivot_table(index='date', columns='client_type', values='fut_stk_net', aggfunc='sum').fillna(0)
        pivot_opt_idx_ce = df.pivot_table(index='date', columns='client_type', values='opt_idx_ce_net', aggfunc='sum').fillna(0)
        pivot_opt_idx_pe = df.pivot_table(index='date', columns='client_type', values='opt_idx_pe_net', aggfunc='sum').fillna(0)
        pivot_opt_stk_ce = df.pivot_table(index='date', columns='client_type', values='opt_stk_ce_net', aggfunc='sum').fillna(0)
        pivot_opt_stk_pe = df.pivot_table(index='date', columns='client_type', values='opt_stk_pe_net', aggfunc='sum').fillna(0)

        if not pivot_idx.index.is_unique:
            pivot_idx = pivot_idx.groupby(level=0).sum()
            pivot_stk = pivot_stk.groupby(level=0).sum()
            pivot_opt_idx_ce = pivot_opt_idx_ce.groupby(level=0).sum()
            pivot_opt_idx_pe = pivot_opt_idx_pe.groupby(level=0).sum()
            pivot_opt_stk_ce = pivot_opt_stk_ce.groupby(level=0).sum()
            pivot_opt_stk_pe = pivot_opt_stk_pe.groupby(level=0).sum()

        dt_dates = pd.to_datetime(dates)
        pivot_idx.index = pd.to_datetime(pivot_idx.index)
        pivot_stk.index = pd.to_datetime(pivot_stk.index)
        pivot_opt_idx_ce.index = pd.to_datetime(pivot_opt_idx_ce.index)
        pivot_opt_idx_pe.index = pd.to_datetime(pivot_opt_idx_pe.index)
        pivot_opt_stk_ce.index = pd.to_datetime(pivot_opt_stk_ce.index)
        pivot_opt_stk_pe.index = pd.to_datetime(pivot_opt_stk_pe.index)

        pivot_idx = pivot_idx.reindex(dt_dates).fillna(0)
        pivot_stk = pivot_stk.reindex(dt_dates).fillna(0)
        pivot_opt_idx_ce = pivot_opt_idx_ce.reindex(dt_dates).fillna(0)
        pivot_opt_idx_pe = pivot_opt_idx_pe.reindex(dt_dates).fillna(0)
        pivot_opt_stk_ce = pivot_opt_stk_ce.reindex(dt_dates).fillna(0)
        pivot_opt_stk_pe = pivot_opt_stk_pe.reindex(dt_dates).fillna(0)
    except Exception as e:
        import logging
        logging.error(f"Error pivoting participant oi: {e}")
        pivot_idx = pd.DataFrame(index=pd.to_datetime(dates))
        pivot_stk = pd.DataFrame(index=pd.to_datetime(dates))
        pivot_opt_idx_ce = pd.DataFrame(index=pd.to_datetime(dates))
        pivot_opt_idx_pe = pd.DataFrame(index=pd.to_datetime(dates))
        pivot_opt_stk_ce = pd.DataFrame(index=pd.to_datetime(dates))
        pivot_opt_stk_pe = pd.DataFrame(index=pd.to_datetime(dates))

    from sqlalchemy import text

    # Fetch NIFTY index data for overlay
    nifty_query = text("""
        SELECT trade_date, close_price
        FROM bhavcopy_fo
        WHERE ticker_symb = 'NIFTY' AND instrument_type = 'FUTIDX'
        AND trade_date = expiry_date
        AND trade_date IN :dates
    """)
    nifty_records = db.execute(nifty_query, {"dates": tuple(dates)}).fetchall()

    # Map NIFTY prices to the same date index
    nifty_prices = {r.trade_date: r.close_price for r in nifty_records}
    nifty_close_list = [nifty_prices.get(d.date(), 0.0) for d in pivot_idx.index]

    return {
        "dates": [d.strftime('%Y-%m-%d') for d in pivot_idx.index],
        "fii_fut_idx": pivot_idx.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "fii_fut_stk": pivot_stk.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "fii_opt_idx_ce": pivot_opt_idx_ce.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "fii_opt_idx_pe": pivot_opt_idx_pe.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "dii_fut_idx": pivot_idx.get('DII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "dii_fut_stk": pivot_stk.get('DII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "dii_opt_idx_ce": pivot_opt_idx_ce.get('DII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "dii_opt_idx_pe": pivot_opt_idx_pe.get('DII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "pro_fut_idx": pivot_idx.get('Pro', pd.Series(0, index=pivot_idx.index)).tolist(),
        "pro_fut_stk": pivot_stk.get('Pro', pd.Series(0, index=pivot_idx.index)).tolist(),
        "pro_opt_idx_ce": pivot_opt_idx_ce.get('Pro', pd.Series(0, index=pivot_idx.index)).tolist(),
        "pro_opt_idx_pe": pivot_opt_idx_pe.get('Pro', pd.Series(0, index=pivot_idx.index)).tolist(),
        "client_fut_idx": pivot_idx.get('Client', pd.Series(0, index=pivot_idx.index)).tolist(),
        "client_fut_stk": pivot_stk.get('Client', pd.Series(0, index=pivot_idx.index)).tolist(),
        "client_opt_idx_ce": pivot_opt_idx_ce.get('Client', pd.Series(0, index=pivot_idx.index)).tolist(),
        "client_opt_idx_pe": pivot_opt_idx_pe.get('Client', pd.Series(0, index=pivot_idx.index)).tolist(),
        "fii_opt_stk_ce": pivot_opt_stk_ce.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "fii_opt_stk_pe": pivot_opt_stk_pe.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "dii_opt_stk_ce": pivot_opt_stk_ce.get('DII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "dii_opt_stk_pe": pivot_opt_stk_pe.get('DII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "pro_opt_stk_ce": pivot_opt_stk_ce.get('Pro', pd.Series(0, index=pivot_idx.index)).tolist(),
        "pro_opt_stk_pe": pivot_opt_stk_pe.get('Pro', pd.Series(0, index=pivot_idx.index)).tolist(),
        "client_opt_stk_ce": pivot_opt_stk_ce.get('Client', pd.Series(0, index=pivot_idx.index)).tolist(),
        "client_opt_stk_pe": pivot_opt_stk_pe.get('Client', pd.Series(0, index=pivot_idx.index)).tolist(),
        "nifty_close": nifty_close_list
    }

@router.get("/api/market-activity/long-short-ratio")
async def get_long_short_ratios(days: int = 30, db: Session = Depends(get_db)):
    """
    Returns Historical Long/Short ratios for each participant across each instrument type.
    Ratio = Long / Short (or Long / (Long+Short)) depending on convention. Here we use Long / Short.
    If Short is 0, we'll cap it or return Long value.
    """
    from backend.ingest.nse_models import FAOParticipantOI
    import pandas as pd

    try:
        dates = db.query(FAOParticipantOI.trade_date).distinct().order_by(FAOParticipantOI.trade_date.desc()).limit(days).all()
        dates = sorted([d[0] for d in dates])
    except Exception:
        dates = []

    if not dates:
        return {}

    records = db.query(FAOParticipantOI).filter(FAOParticipantOI.trade_date.in_(dates)).all()

    df = pd.DataFrame([{
        'date': r.trade_date,
        'client_type': r.client_type,
        'fut_idx_long': r.future_index_long,
        'fut_idx_short': r.future_index_short,
        'fut_stk_long': r.future_stock_long,
        'fut_stk_short': r.future_stock_short,
        'opt_idx_ce_long': r.option_index_call_long,
        'opt_idx_ce_short': r.option_index_call_short,
        'opt_idx_pe_long': r.option_index_put_long,
        'opt_idx_pe_short': r.option_index_put_short,
        'opt_stk_ce_long': r.option_stock_call_long,
        'opt_stk_ce_short': r.option_stock_call_short,
        'opt_stk_pe_long': r.option_stock_put_long,
        'opt_stk_pe_short': r.option_stock_put_short
    } for r in records])

    if df.empty:
        return {}

    # Normalize client types
    df['client_type'] = df['client_type'].str.upper()
    df.loc[df['client_type'] == 'PRO', 'client_type'] = 'Pro'
    df.loc[df['client_type'] == 'CLIENT', 'client_type'] = 'Client'

    # Calculate ratios
    import numpy as np

    # Vectorized safe division. If both 0, ratio is 1.0. If short is 0 but long is > 0, we'll cap the ratio at a high sensible number like long * 2 or just raw long.
    # To keep it simple and mathematically sound: If Short=0 and Long=0 -> 1.0. If Short=0 and Long>0 -> Long.
    for inst in ['fut_idx', 'fut_stk', 'opt_idx_ce', 'opt_idx_pe', 'opt_stk_ce', 'opt_stk_pe']:
        df[f'{inst}_ratio'] = np.where(
            (df[f'{inst}_short'] == 0) & (df[f'{inst}_long'] == 0), 1.0,
            np.where(
                df[f'{inst}_short'] == 0, df[f'{inst}_long'],
                df[f'{inst}_long'] / df[f'{inst}_short']
            )
        )

    result = {"dates": [d.strftime('%Y-%m-%d') for d in pd.to_datetime(dates)]}

    for p in ['FII', 'DII', 'Pro', 'Client']:
        p_df = df[df['client_type'] == p].set_index('date').reindex(dates).fillna(1.0)
        result[f"{p.lower()}_fut_idx"] = p_df['fut_idx_ratio'].round(2).tolist()
        result[f"{p.lower()}_fut_stk"] = p_df['fut_stk_ratio'].round(2).tolist()
        result[f"{p.lower()}_opt_idx_ce"] = p_df['opt_idx_ce_ratio'].round(2).tolist()
        result[f"{p.lower()}_opt_idx_pe"] = p_df['opt_idx_pe_ratio'].round(2).tolist()
        result[f"{p.lower()}_opt_stk_ce"] = p_df['opt_stk_ce_ratio'].round(2).tolist()
        result[f"{p.lower()}_opt_stk_pe"] = p_df['opt_stk_pe_ratio'].round(2).tolist()

    return result

@router.get("/api/market-activity/smart-vs-retail")
async def get_smart_money_vs_retail(db: Session = Depends(get_db)):
    """
    Returns the Smart Money (FII+DII+Pro) vs Retail (Client) totals for the latest available date.
    Calculates net positions (Long - Short) for each instrument.
    """
    from backend.ingest.nse_models import FAOParticipantOI
    from sqlalchemy import func

    latest_date_tuple = db.query(func.max(FAOParticipantOI.trade_date)).first()
    if not latest_date_tuple or not latest_date_tuple[0]:
        return {}
    latest_date = latest_date_tuple[0]

    records = db.query(FAOParticipantOI).filter(FAOParticipantOI.trade_date == latest_date).all()

    smart_money = {'fut_idx': 0, 'fut_stk': 0, 'opt_idx_ce': 0, 'opt_idx_pe': 0}
    retail = {'fut_idx': 0, 'fut_stk': 0, 'opt_idx_ce': 0, 'opt_idx_pe': 0}

    for r in records:
        ctype = r.client_type.upper()
        target = retail if ctype == 'CLIENT' else smart_money

        target['fut_idx'] += (r.future_index_long - r.future_index_short)
        target['fut_stk'] += (r.future_stock_long - r.future_stock_short)
        target['opt_idx_ce'] += (r.option_index_call_long - r.option_index_call_short)
        target['opt_idx_pe'] += (r.option_index_put_long - r.option_index_put_short)

    return {
        "date": latest_date.strftime('%Y-%m-%d'),
        "smart_money": smart_money,
        "retail": retail
    }


@router.get("/api/market-activity/cash-flow")
async def get_cash_market_flow(days: int = 30, db: Session = Depends(get_db)):
    """
    Returns real FII/DII Cash Market Flow from the database over the last X days.
    """
    from backend.ingest.nse_models import FIIDIICash

    try:
        dates_query = db.query(FIIDIICash.trade_date).distinct().order_by(FIIDIICash.trade_date.desc()).limit(days).all()
        dates = [d[0] for d in dates_query]
        dates.sort()
    except Exception as e:
        dates = []

    import pandas as pd
    import numpy as np
    from datetime import date, timedelta

    if not dates:
         return {"dates": []}

    records = db.query(FIIDIICash).filter(FIIDIICash.trade_date.in_(dates)).all()

    df = pd.DataFrame([{
        'date': r.trade_date,
        'category': r.category,
        'net_value': r.net_value
    } for r in records])

    if df.empty:
         return {"dates": []}


    try:
        pivot = df.pivot_table(index='date', columns='category', values='net_value', aggfunc='sum').fillna(0)

        if not pivot.index.is_unique:
            pivot = pivot.groupby(level=0).sum()

        dt_dates = pd.to_datetime(dates)
        pivot.index = pd.to_datetime(pivot.index)
        pivot = pivot.reindex(dt_dates).fillna(0)
    except Exception as e:
        import logging
        logging.error(f"Error pivoting cash market flow: {e}")
        pivot = pd.DataFrame(index=pd.to_datetime(dates))

    from sqlalchemy import text

    # Fetch NIFTY index data for overlay
    nifty_query = text("""
        SELECT trade_date, close_price
        FROM bhavcopy_fo
        WHERE ticker_symb = 'NIFTY' AND instrument_type = 'FUTIDX'
        AND trade_date = expiry_date
        AND trade_date IN :dates
    """)
    nifty_records = db.execute(nifty_query, {"dates": tuple(dates)}).fetchall()

    # Map NIFTY prices to the same date index
    nifty_prices = {r.trade_date: r.close_price for r in nifty_records}
    nifty_close_list = [nifty_prices.get(d.date(), 0.0) for d in pivot.index]

    return {
        "dates": [d.strftime('%Y-%m-%d') for d in pivot.index],
        "fii_net": pivot.get('FII', pd.Series(0, index=pivot.index)).tolist(),
        "dii_net": pivot.get('DII', pd.Series(0, index=pivot.index)).tolist(),
        "nifty_close": nifty_close_list
    }
