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
    records = db.query(DailyDerivativesAnalysis).filter(
        DailyDerivativesAnalysis.trade_date == target_date
    ).order_by(DailyDerivativesAnalysis.mwpl_utilization_pct.desc()).all()

    if not records:
        return []

    result = []
    for r in records:
        d = dict(r.__dict__)
        d.pop('_sa_instance_state', None)
        result.append(d)

    return result

@router.get("/api/morning-report/timeseries")
async def get_report_timeseries(symbol: str, limit: int = 100, db: Session = Depends(get_db)):
    from backend.ingest.nse_models import DailyDerivativesAnalysis

    records = db.query(DailyDerivativesAnalysis).filter(
        DailyDerivativesAnalysis.symbol == symbol.upper()
    ).order_by(DailyDerivativesAnalysis.trade_date.desc()).limit(limit).all()

    if not records:
        return []

    result = []
    for r in records:
        d = dict(r.__dict__)
        d.pop('_sa_instance_state', None)
        d['trade_date'] = str(d['trade_date'])
        result.append(d)

    return result
